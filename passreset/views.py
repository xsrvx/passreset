from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, ALL, Tls
from ldap3.core.exceptions import LDAPException
from .password_generator import generate_password
import urllib.parse
import logging
import ssl

# Get an instance of a logger
logger = logging.getLogger('ldap')

def establish_ldap_connection():
    try:
        ldap_server = '10.1.1.36'  # DC1
        ldap_port = 636
        ldap_user = 'username@flaglercps.net'
        ldap_password = 'passwordhere'

        logger.debug("Establishing LDAP connection with SSL...")

        # Ignore cert validation
        tls = Tls(validate=ssl.CERT_NONE)
        server = Server(ldap_server, port=ldap_port, use_ssl=True, tls=tls, get_info=ALL)

        conn = Connection(server, user=ldap_user, password=ldap_password, auto_bind=True)
        
        logger.info("LDAP connection established successfully with SSL.")
        return conn
    except Exception as e:
        logger.error("Error establishing LDAP connection: %s", e)
        raise

def close_ldap_connection(conn):
    if conn:
        logger.debug("Closing LDAP connection...")
        conn.unbind()
        logger.info("LDAP connection closed.")

def home_view(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            return redirect('search_users', query=query)
    return render(request, 'home.html')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if authenticate(request, username=username, password=password):
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'login.html')

def generate_and_change_password_view(request, username, user_dn):
    conn = None
    try:
        generated_password = generate_password()
        conn = establish_ldap_connection()
        user_dn = urllib.parse.unquote(user_dn)
        logger.debug("Attempting to change password for user DN: %s", user_dn)
        
        new_password = f'"{generated_password}"'
        password_value = new_password.encode('utf-16-le')
        
        success = conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [password_value])]})
        
        if not success:
            logger.error(f"Failed to change password for {user_dn}. Detail: {conn.result['description']}")
            return JsonResponse({'success': False, 'error': conn.result['description']}, status=500)
        
        logger.info("Password changed successfully for user DN: %s", user_dn)
        return JsonResponse({'success': True, 'generated_password': generated_password, 'message': 'Password changed successfully'})

    except LDAPException as e:
        logger.error("LDAP error during password change: %s", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error("General error during password change: %s", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        close_ldap_connection(conn)

def generate_password_view(request):
    try:
        generated_password = generate_password()
        return JsonResponse({'success': True, 'generated_password': generated_password})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def search_users(request, query):
    conn = None
    try:
        conn = establish_ldap_connection()
        
        logger.debug(f"Starting LDAP search for query: {query}")
        
        search_base = 'dc=flaglercps,dc=net'
        search_filter = f"(sAMAccountName={query})"
        
        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['givenName', 'sn', 'sAMAccountName', 'distinguishedName']
        )
        
        if conn.entries:
            logger.info(f"Search returned {len(conn.entries)} entries.")
        else:
            logger.info("Search returned no entries.")
        
        html_content = '<div class="contact-cards">'
        
        if conn.entries:
            for entry in conn.entries:
                logger.debug(f"Entry attributes: {entry.entry_attributes_as_dict}")
                
                given_name = entry['givenName'].value if 'givenName' in entry else ''
                last_name = entry['sn'].value if 'sn' in entry else ''
                username = entry['sAMAccountName'].value if 'sAMAccountName' in entry else ''
                user_dn = entry['distinguishedName'].value if 'distinguishedName' in entry else ''
                
                html_content += f'''
                    <div class="contact-card">
                        <div class="user-info">
                            <img src="/static/admin/img/user_icon.png" alt="User Icon" class="user-icon" width="142" height="142">
                            <div class="contact-details">
                                <p><strong>First Name:</strong> {given_name}</p>
                                <p><strong>Last Name:</strong> {last_name}</p>
                                <p><strong>Username:</strong> {username}</p>
                                <p><strong>Password:</strong> <span id="generated-password-{username}"></span></p> <!-- Password field -->
                                <button class="generate-button" onclick="generateAndChangePassword('{username}', '{user_dn}')">Generate</button>
                            </div>
                        </div>
                    </div>
                '''
        else:
            html_content += "<p>No results found for your query.</p>"
        
        html_content += '</div>'
        
        close_ldap_connection(conn)
        
        return HttpResponse(html_content)

    except Exception as e:
        if conn:
            close_ldap_connection(conn)
        logger.error("LDAP Error during search: %s", e)
        return HttpResponse('LDAP Error occurred', status=500)
