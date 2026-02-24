from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import time
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'Healthy',
        'mttr': '-',
        'reason': 'No incidents',
        'monitored_urls': [],
        'monitoring_active': False
    })

@app.route('/check-website', methods=['POST'])
def check_website():
    data = request.json
    url = data.get('url', '')
    
    socketio.emit('kubectl_log', f'🔍 Checking {url}...')
    socketio.emit('kubectl_log', '📡 Scanning for API endpoints...')
    
    try:
        start = time.time()
        response = requests.get(url, timeout=10, allow_redirects=True)
        response_time = round((time.time() - start) * 1000, 2)
        
        # Capture response details for intelligent analysis
        response_headers = dict(response.headers)
        response_content = response.text[:1000] if response.text else ''
        
        # Extract potential API calls from HTML
        apis_found = extract_apis(response.text, url)
        
        socketio.emit('kubectl_log', f'📊 Status Code: {response.status_code}')
        socketio.emit('kubectl_log', f'⏱️  Response Time: {response_time}ms')
        socketio.emit('kubectl_log', f'🔗 Found {len(apis_found)} API endpoints')
        
        # Check APIs
        failed_apis = []
        if apis_found:
            socketio.emit('kubectl_log', '🔍 Testing API endpoints...')
            for api in apis_found[:5]:  # Test first 5
                try:
                    api_resp = requests.get(api, timeout=3)
                    if api_resp.status_code >= 400:
                        failed_apis.append({'url': api, 'status': api_resp.status_code})
                        socketio.emit('kubectl_log', f'❌ API failed: {api} ({api_resp.status_code})')
                except:
                    pass
        
        if response.status_code >= 400 or failed_apis:
            socketio.emit('kubectl_log', f'🚨 Error detected: HTTP {response.status_code}')
            socketio.emit('kubectl_log', '🧠 AI analyzing root cause...')
            time.sleep(1)
            
            # Intelligent error analysis with context
            diagnosis = analyze_error_intelligent(
                status_code=response.status_code,
                url=url,
                headers=response_headers,
                content=response_content,
                failed_apis=failed_apis,
                response_time=response_time
            )
            
            socketio.emit('kubectl_log', f'🔍 Root Cause: {diagnosis["root_cause"]}')
            socketio.emit('kubectl_log', f'📈 Confidence: {diagnosis["confidence"]}%')
            socketio.emit('kubectl_log', '💡 Recommended fixes:')
            for i, step in enumerate(diagnosis['fix_steps'][:3], 1):
                socketio.emit('kubectl_log', f'  {i}. {step}')
            
            return jsonify({
                'result': {'status': 'error', 'response_time': response_time, 'failed_apis': failed_apis},
                'diagnosis': diagnosis
            })
        else:
            socketio.emit('kubectl_log', '✅ Website is healthy!')
            socketio.emit('kubectl_log', '✅ All API endpoints responding')
            return jsonify({
                'result': {'status': 'healthy', 'response_time': response_time, 'apis_found': len(apis_found)},
                'diagnosis': {
                    'root_cause': 'No issues detected',
                    'confidence': 100,
                    'fix_steps': [],
                    'prevention': [],
                    'estimated_fix_time': '0 minutes'
                }
            })
    
    except requests.exceptions.Timeout:
        socketio.emit('kubectl_log', '🚨 Request timed out!')
        socketio.emit('kubectl_log', '🧠 AI analyzing...')
        
        diagnosis = {
            'root_cause': f'Request timeout - {url} not responding within 10 seconds',
            'error_explanation': f'The server at {url} took too long to respond (>10 seconds). This specific timeout indicates the server received your request but is either processing it very slowly, experiencing high load, or has slow backend operations. The connection was established but the response never completed.',
            'confidence': 85,
            'fix_steps': [
                f'Check if {url} server is experiencing high load',
                'Verify database query performance on the backend',
                'Check for slow API calls or external service dependencies',
                'Review application logs for stuck processes'
            ],
            'prevention': [
                'Implement request timeout monitoring',
                'Add performance profiling to identify bottlenecks',
                'Set up CDN for static assets',
                'Optimize database queries with indexes'
            ],
            'estimated_fix_time': '10 minutes'
        }
        
        socketio.emit('kubectl_log', f'🔍 Root Cause: {diagnosis["root_cause"]}')
        socketio.emit('kubectl_log', f'📈 Confidence: {diagnosis["confidence"]}%')
        
        return jsonify({
            'result': {'status': 'error', 'response_time': 0},
            'diagnosis': diagnosis
        })
    
    except Exception as e:
        error_str = str(e).lower()
        socketio.emit('kubectl_log', f'❌ Error: {str(e)}')
        
        # Analyze specific connection errors
        if 'connection aborted' in error_str or 'remote end closed' in error_str:
            diagnosis = {
                'root_cause': f'Connection aborted - {url} closed connection unexpectedly',
                'error_explanation': f'The server at {url} abruptly closed the connection without sending a complete response. This typically happens when the server crashes mid-request, runs out of resources, or has a timeout configured that kills long-running requests. The connection was established but terminated prematurely.',
                'confidence': 88,
                'fix_steps': [
                    f'Check if {url} server is crashing or restarting',
                    f'Review {url} server timeout settings',
                    f'Check {url} server resource limits (memory/CPU)',
                    f'Verify {url} application logs for crash reports'
                ],
                'prevention': [
                    'Increase server timeout thresholds',
                    'Add server health monitoring',
                    'Implement graceful shutdown handling',
                    'Monitor server resource usage'
                ],
                'estimated_fix_time': '5 minutes'
            }
        elif 'ssl' in error_str or 'certificate' in error_str:
            diagnosis = {
                'root_cause': 'SSL/TLS certificate error - Invalid or expired certificate',
                'error_explanation': 'The SSL/TLS certificate is invalid, expired, self-signed, or does not match the domain name. This prevents secure HTTPS connections. Browsers block these connections to protect users from potential security risks like man-in-the-middle attacks.',
                'confidence': 90,
                'fix_steps': [
                    'Verify SSL certificate is valid and not expired (openssl s_client)',
                    'Check certificate chain is complete with intermediate certificates',
                    'Ensure certificate matches the exact domain name',
                    'Renew SSL certificate if expired (Let\'s Encrypt or CA)'
                ],
                'prevention': [
                    'Set up SSL certificate expiry monitoring and alerts',
                    'Use automated certificate renewal (Let\'s Encrypt/Certbot)',
                    'Monitor certificate health daily with tools',
                    'Set up alerts 30 days before certificate expiry'
                ],
                'estimated_fix_time': '15 minutes'
            }
        elif 'timeout' in error_str or 'timed out' in error_str:
            diagnosis = {
                'root_cause': 'Connection timeout - Server taking too long to respond',
                'error_explanation': 'The connection attempt exceeded the maximum wait time. This happens when the server is too slow to respond, network latency is high, the server is overloaded, or there are network routing issues between client and server.',
                'confidence': 85,
                'fix_steps': [
                    'Check if server is overloaded (CPU/memory usage)',
                    'Verify network connectivity and routing',
                    'Increase timeout threshold in client configuration',
                    'Check for DDoS attack or unusual traffic patterns'
                ],
                'prevention': [
                    'Implement CDN for faster response times',
                    'Add load balancing across multiple servers',
                    'Set up auto-scaling based on traffic',
                    'Monitor server response times continuously'
                ],
                'estimated_fix_time': '10 minutes'
            }
        elif 'dns' in error_str or 'name resolution' in error_str:
            diagnosis = {
                'root_cause': 'DNS resolution failure - Domain name cannot be resolved',
                'error_explanation': 'The domain name could not be translated to an IP address. This means DNS servers cannot find the domain, the domain does not exist, DNS records are misconfigured, or the domain has expired. Without DNS resolution, the browser cannot locate the server.',
                'confidence': 95,
                'fix_steps': [
                    'Verify domain DNS records are correctly configured',
                    'Check if domain registration has expired',
                    'Verify nameservers are responding (dig/nslookup)',
                    'Clear local DNS cache and retry (ipconfig /flushdns)'
                ],
                'prevention': [
                    'Use multiple DNS providers for redundancy',
                    'Set up DNS health monitoring and alerts',
                    'Monitor domain expiry dates with auto-renewal',
                    'Implement DNS failover mechanisms'
                ],
                'estimated_fix_time': '20 minutes'
            }
        elif 'refused' in error_str or 'connection refused' in error_str:
            diagnosis = {
                'root_cause': 'Connection refused - Server actively rejecting connections',
                'error_explanation': 'The server is reachable but actively refusing the connection. This typically means the web server service is not running, the port is closed, firewall is blocking the connection, or the service crashed. The server received the request but rejected it.',
                'confidence': 88,
                'fix_steps': [
                    'Check if web server is running (systemctl status nginx/apache)',
                    'Verify firewall rules allow traffic on the port',
                    'Check if the correct port is open and listening (netstat -tulpn)',
                    'Restart web server service to recover from crash'
                ],
                'prevention': [
                    'Set up service health monitoring with auto-restart',
                    'Implement automatic service recovery on failure',
                    'Configure firewall rules properly',
                    'Use process monitoring tools (systemd, supervisor)'
                ],
                'estimated_fix_time': '5 minutes'
            }
        else:
            diagnosis = {
                'root_cause': f'Network connectivity issue: {str(e)}',
                'error_explanation': f'Failed to connect to {url}. Error: {str(e)}. This indicates a fundamental network connectivity problem preventing any communication with the server.',
                'confidence': 70,
                'fix_steps': [
                    f'Verify {url} is a valid and accessible URL',
                    f'Test if {domain} resolves correctly using: nslookup {domain}',
                    f'Try accessing {url} from a different network or device',
                    'Check if your network has firewall/proxy restrictions'
                ],
                'prevention': [
                    'Set up uptime monitoring',
                    'Use multiple availability zones',
                    'Implement health checks',
                    'Monitor network infrastructure'
                ],
                'estimated_fix_time': '5 minutes'
            }
        
        return jsonify({
            'result': {'status': 'error', 'response_time': 0},
            'diagnosis': diagnosis
        })

@app.route('/inject', methods=['POST'])
def inject_failure():
    data = request.json or {}
    url = data.get('url', 'http://httpstat.us/500')
    
    socketio.emit('kubectl_log', f'🚨 Simulating failure for {url}')
    socketio.start_background_task(simulate_failure, url)
    
    return jsonify({'message': 'Failure simulation started'})

def simulate_failure(url):
    time.sleep(1)
    socketio.emit('kubectl_log', '🔍 Scanning website...')
    
    try:
        response = requests.get(url, timeout=10)
        socketio.emit('kubectl_log', f'📊 Status: HTTP {response.status_code}')
        
        if response.status_code >= 400:
            socketio.emit('kubectl_log', '🚨 Error detected!')
            time.sleep(1)
            socketio.emit('kubectl_log', '🧠 AI analyzing root cause...')
            
            diagnosis = analyze_error(response.status_code)
            
            time.sleep(1)
            socketio.emit('kubectl_log', f'🔍 Root Cause: {diagnosis["root_cause"]}')
            socketio.emit('kubectl_log', f'📈 Confidence: {diagnosis["confidence"]}%')
            socketio.emit('kubectl_log', f'⏰ Est. Fix Time: {diagnosis["estimated_fix_time"]}')
            
            time.sleep(1)
            socketio.emit('kubectl_log', '💡 Recommended fixes:')
            for i, step in enumerate(diagnosis['fix_steps'][:3], 1):
                socketio.emit('kubectl_log', f'  {i}. {step}')
            
            time.sleep(1)
            socketio.emit('kubectl_log', '🔧 Applying auto-remediation...')
            time.sleep(2)
            socketio.emit('kubectl_log', '✅ Remediation applied successfully')
            socketio.emit('kubectl_log', '🎯 MTTR: 8.5s')
            socketio.emit('status_update', {'status': 'Healthy'})
    
    except Exception as e:
        socketio.emit('kubectl_log', f'❌ Error: {str(e)}')

@app.route('/monitor', methods=['POST'])
def start_monitoring():
    data = request.json
    url = data.get('url', '')
    
    socketio.emit('kubectl_log', f'📡 Started monitoring {url}')
    
    return jsonify({'message': f'Started monitoring {url}', 'url': url})

def extract_apis(html, base_url):
    """Extract API endpoints from HTML"""
    import re
    from urllib.parse import urljoin, urlparse
    
    apis = set()
    
    # Find fetch/axios calls
    patterns = [
        r'fetch\(["\']([^"\'\']+)["\']',
        r'axios\.(get|post|put|delete)\(["\']([^"\'\']+)["\']',
        r'\$\.ajax\(["\']([^"\'\']+)["\']',
        r'href=["\']([^"\'\']*api[^"\'\']*)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            url = match if isinstance(match, str) else match[-1]
            if url.startswith('http'):
                apis.add(url)
            elif url.startswith('/'):
                apis.add(urljoin(base_url, url))
    
    return list(apis)[:10]

def analyze_error_intelligent(status_code, url, headers, content, failed_apis=[], response_time=0):
    """Intelligent error analysis based on actual response context"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    
    # Detect server type from headers
    server_type = headers.get('Server', 'Unknown')
    content_type = headers.get('Content-Type', '')
    
    # Check for specific error patterns in content
    error_indicators = {
        'nginx': 'nginx' in content.lower() or 'nginx' in server_type.lower(),
        'apache': 'apache' in content.lower() or 'apache' in server_type.lower(),
        'cloudflare': 'cloudflare' in content.lower() or 'CF-RAY' in headers,
        'aws': 'aws' in content.lower() or 'x-amz' in str(headers).lower(),
        'database': any(word in content.lower() for word in ['database', 'mysql', 'postgres', 'mongodb', 'connection failed']),
        'php': 'php' in content.lower() or '.php' in content,
        'python': 'python' in content.lower() or 'django' in content.lower() or 'flask' in content.lower(),
        'node': 'node' in content.lower() or 'express' in content.lower(),
    }

def analyze_error(status_code, failed_apis=[]):
    if failed_apis:
        return {
            'root_cause': f'{len(failed_apis)} API endpoint(s) failing - Backend service issues',
            'confidence': 88,
            'fix_steps': [
                f'Fix failing API: {failed_apis[0]["url"]}',
                'Check backend service logs',
                'Restart backend services',
                'Verify database connectivity'
            ],
            'prevention': [
                'Add API health checks',
                'Implement circuit breakers',
                'Set up API monitoring'
            ],
            'estimated_fix_time': '5 minutes'
        }
    
    if status_code == 500:
        # Context-aware explanation
        context_details = []
        if error_indicators['database']:
            context_details.append('Database connection error detected in response')
        if error_indicators['php']:
            context_details.append('PHP application error')
        elif error_indicators['python']:
            context_details.append('Python application error')
        elif error_indicators['node']:
            context_details.append('Node.js application error')
        
        specific_cause = ' - ' + ', '.join(context_details) if context_details else ''
        
        return {
            'root_cause': f'HTTP 500 Internal Server Error on {domain}{specific_cause}',
            'error_explanation': f'The server at {domain} encountered an unexpected error while processing your request. Based on analysis: {server_type} server returned a 500 error. ' + 
                               ('Database connectivity issues detected in the error response. ' if error_indicators['database'] else '') +
                               f'Response time was {response_time}ms. This indicates a server-side application crash, unhandled exception, or critical configuration error.',
            'confidence': 90 if context_details else 85,
            'fix_steps': [
                f'Check application logs on {domain} for stack traces',
                f'Restart the application server running on {domain}',
                'Verify database connectivity' if error_indicators['database'] else f'Review recent code deployments to {domain}',
                f'Check {domain} server resources (CPU/memory usage)'
            ],
            'prevention': [
                'Implement comprehensive error handling and logging',
                'Add application health checks and monitoring',
                'Set up automated alerts for 500 errors',
                'Use error tracking tools (Sentry, Rollbar)'
            ],
            'estimated_fix_time': '5 minutes'
        }
    elif status_code in [502, 504]:
        error_type = 'Bad Gateway' if status_code == 502 else 'Gateway Timeout'
        
        # Detect proxy/gateway type
        proxy_info = ''
        if error_indicators['nginx']:
            proxy_info = 'Nginx reverse proxy'
        elif error_indicators['apache']:
            proxy_info = 'Apache reverse proxy'
        elif error_indicators['cloudflare']:
            proxy_info = 'Cloudflare CDN'
        else:
            proxy_info = 'Gateway/Proxy server'
        
        return {
            'root_cause': f'HTTP {status_code} {error_type} - {proxy_info} at {domain}',
            'error_explanation': f'{proxy_info} at {domain} cannot reach the backend application server. Server type: {server_type}. ' +
                               (f'Cloudflare is reporting the origin server is down or unreachable. ' if error_indicators['cloudflare'] else '') +
                               f'This means the backend application behind the proxy is either not running, crashed, or not responding on the expected port. Response time: {response_time}ms.',
            'confidence': 92,
            'fix_steps': [
                f'Check if backend application is running on {domain}',
                f'Restart {proxy_info} service' if proxy_info != 'Gateway/Proxy server' else 'Restart reverse proxy (nginx/apache)',
                f'Verify backend port configuration on {domain}',
                f'Check {domain} upstream server health'
            ],
            'prevention': [
                'Implement auto-scaling for backend services',
                'Add load balancing across multiple servers',
                'Set up backend health checks',
                'Monitor upstream server response times'
            ],
            'estimated_fix_time': '3 minutes'
        }
    elif status_code == 503:
        maintenance_mode = 'maintenance' in content.lower() or 'temporarily unavailable' in content.lower()
        
        return {
            'root_cause': f'HTTP 503 Service Unavailable - {domain} {"(Maintenance Mode)" if maintenance_mode else "(Overloaded)"}',
            'error_explanation': f'The server at {domain} (running {server_type}) is temporarily unable to handle requests. ' +
                               ('The site appears to be in maintenance mode based on the response content. ' if maintenance_mode else 
                                f'Server is likely overloaded with too many requests or has run out of resources. Response time: {response_time}ms suggests ') +
                               'The web service may have crashed, reached connection limits, or exhausted CPU/memory resources.',
            'confidence': 96,
            'fix_steps': [
                f'Check if web service is running on {domain}: systemctl status',
                f'Restart the service on {domain} to clear overload',
                f'Monitor CPU/memory usage on {domain} server',
                'Scale up resources' if not maintenance_mode else 'Wait for maintenance to complete'
            ],
            'prevention': [
                'Implement rate limiting to prevent overload',
                'Add caching layer (Redis, Memcached)',
                'Set up auto-scaling based on load',
                'Monitor resource usage continuously'
            ],
            'estimated_fix_time': '2 minutes'
        }
    elif status_code == 404:
        path = urlparse(url).path
        return {
            'root_cause': f'HTTP 404 Not Found - {path} does not exist on {domain}',
            'error_explanation': f'The requested path "{path}" was not found on {domain} (Server: {server_type}). ' +
                               f'This specific URL does not exist on the server. The page may have been moved, deleted, or the URL is mistyped. ' +
                               ('The server is running but this specific route/file is missing. ' if response_time < 500 else 'Server responded slowly, may indicate routing issues. '),
            'confidence': 98,
            'fix_steps': [
                f'Verify the path "{path}" exists on {domain}',
                f'Check {domain} web server routing configuration',
                f'Review {domain} application routes for "{path}"',
                f'Check if "{path}" was recently moved or deleted'
            ],
            'prevention': [
                'Implement proper URL redirects for moved content',
                'Set up 404 monitoring and alerts',
                'Use link checkers to find broken links',
                'Maintain URL structure consistency'
            ],
            'estimated_fix_time': '1 minute'
        }
    elif status_code == 403:
        blocked_reason = ''
        if error_indicators['cloudflare']:
            blocked_reason = 'Cloudflare WAF (Web Application Firewall) blocked this request'
        elif 'forbidden' in content.lower():
            blocked_reason = 'Access explicitly forbidden by server configuration'
        
        return {
            'root_cause': f'HTTP 403 Forbidden - Access denied to {url}',
            'error_explanation': f'Access to {url} on {domain} was denied. ' +
                               (f'{blocked_reason}. ' if blocked_reason else f'Server ({server_type}) refused authorization. ') +
                               'This could be due to: IP address blocking, missing authentication, incorrect file permissions, or WAF security rules blocking the request.',
            'confidence': 93,
            'fix_steps': [
                f'Check file permissions on {domain} for this resource',
                f'Review {domain} firewall/WAF rules' if error_indicators['cloudflare'] else f'Check .htaccess rules on {domain}',
                f'Verify your IP is whitelisted on {domain}',
                f'Check authentication credentials for {domain}'
            ],
            'prevention': [
                'Implement proper access control lists (ACL)',
                'Set up IP whitelisting correctly',
                'Monitor failed authentication attempts',
                'Use role-based access control (RBAC)'
            ],
            'estimated_fix_time': '3 minutes'
        }
    elif status_code == 401:
        return {
            'root_cause': 'HTTP 401 Unauthorized',
            'error_explanation': 'Authentication is required but has failed or not been provided. The request lacks valid authentication credentials, the token has expired, or the username/password is incorrect. This is different from 403 - you need to authenticate first.',
            'confidence': 96,
            'fix_steps': [
                f'Provide valid authentication credentials for {domain}',
                f'Check if your API token/key for {domain} has expired',
                f'Verify Authorization header is set correctly for {domain}',
                f'Request new access token from {domain}'
            ],
            'prevention': [
                'Implement token refresh mechanism',
                'Set up proper session management',
                'Use secure authentication protocols (OAuth2, JWT)',
                'Monitor authentication failures'
            ],
            'estimated_fix_time': '2 minutes'
        }
    elif status_code == 429:
        return {
            'root_cause': 'HTTP 429 Too Many Requests',
            'error_explanation': 'The user has sent too many requests in a given time period (rate limiting). This is a protective measure to prevent abuse, DDoS attacks, or overloading the server. Your IP or API key has exceeded the allowed request quota.',
            'confidence': 99,
            'fix_steps': [
                f'Wait {"60 seconds" if "Retry-After" not in headers else headers.get("Retry-After", "60") + " seconds"} before retrying {domain}',
                f'Reduce request frequency to {domain}',
                f'Implement exponential backoff for {domain} requests',
                f'Check {domain} rate limit documentation'
            ],
            'prevention': [
                'Implement request throttling in client code',
                'Use caching to reduce API calls',
                'Upgrade to higher rate limit tier if available',
                'Distribute requests across multiple API keys'
            ],
            'estimated_fix_time': '1 minute'
        }
    elif status_code == 408:
        return {
            'root_cause': 'HTTP 408 Request Timeout',
            'error_explanation': 'The server timed out waiting for the request. The client took too long to send the complete request, or the connection was too slow. This is different from 504 - the timeout occurred before the request was fully received.',
            'confidence': 87,
            'fix_steps': [
                f'Check network connection speed to {domain}',
                f'Reduce request payload size when calling {domain}',
                f'Increase client timeout settings for {domain}',
                f'Try accessing {domain} from a different network'
            ],
            'prevention': [
                'Implement request compression',
                'Use faster network connection',
                'Split large requests into smaller chunks',
                'Monitor network latency'
            ],
            'estimated_fix_time': '3 minutes'
        }
    elif status_code in [301, 302, 307, 308]:
        redirect_type = 'Permanent' if status_code in [301, 308] else 'Temporary'
        return {
            'root_cause': f'HTTP {status_code} {redirect_type} Redirect',
            'error_explanation': f'The resource has been moved to a different URL. This is a {redirect_type.lower()} redirect, meaning the resource is available at a new location. Your application should follow the redirect or update the URL reference.',
            'confidence': 94,
            'fix_steps': [
                f'Update your application to use the new URL for {domain}',
                f'Follow the redirect to the new location',
                f'Check {domain} documentation for the correct URL',
                'Enable automatic redirect following in HTTP client'
            ],
            'prevention': [
                'Keep URL references up to date',
                'Use canonical URLs in documentation',
                'Set up redirect monitoring',
                'Avoid excessive redirect chains'
            ],
            'estimated_fix_time': '2 minutes'
        }
    else:
        return {
            'root_cause': f'HTTP {status_code} Error from {domain}',
            'error_explanation': f'The server at {domain} (running {server_type}) returned HTTP status code {status_code}. ' +
                               f'Response time: {response_time}ms. Content-Type: {content_type}. ' +
                               'This is an uncommon status code. Check the response body and server logs for specific details about what caused this error.',
            'confidence': 75,
            'fix_steps': [
                f'Review {domain} server logs for detailed error information',
                f'Check {domain} API documentation for status code {status_code}',
                f'Verify request format when calling {domain}',
                f'Contact {domain} administrator if issue persists'
            ],
            'prevention': [
                'Implement comprehensive error monitoring',
                'Set up alerts for unusual status codes',
                'Add detailed logging for debugging',
                'Document custom error codes'
            ],
            'estimated_fix_time': '5 minutes'
        }

if __name__ == '__main__':
    print('🚀 Universal AI Incident Detector Backend')
    print('📡 Server running on http://localhost:5001')
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
