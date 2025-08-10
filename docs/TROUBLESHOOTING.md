# MindCoach Troubleshooting Guide

This comprehensive guide provides solutions to common issues you may encounter while using MindCoach, organized by category with detailed error messages and step-by-step solutions.

## Table of Contents

1. [Installation and Setup Issues](#installation-and-setup-issues)
2. [Authentication and User Management](#authentication-and-user-management)
3. [Subject Selection Problems](#subject-selection-problems)
4. [Survey Generation and Submission Issues](#survey-generation-and-submission-issues)
5. [Content Generation Pipeline Problems](#content-generation-pipeline-problems)
6. [Lesson Access and Display Issues](#lesson-access-and-display-issues)
7. [Subscription and Payment Problems](#subscription-and-payment-problems)
8. [Performance and Loading Issues](#performance-and-loading-issues)
9. [Mobile and Responsive Design Issues](#mobile-and-responsive-design-issues)
10. [API Integration Problems](#api-integration-problems)
11. [Docker and Deployment Issues](#docker-and-deployment-issues)
12. [Database and File System Issues](#database-and-file-system-issues)

## Installation and Setup Issues

### Problem: Python Dependencies Installation Fails

**Error Messages:**
```
ERROR: Could not find a version that satisfies the requirement langchain
pip install failed with exit code 1
ModuleNotFoundError: No module named 'flask'
```

**Solutions:**
1. **Check Python Version**:
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Update pip and setuptools**:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

3. **Install in Virtual Environment**:
   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Clear pip cache if issues persist**:
   ```bash
   pip cache purge
   pip install -r requirements.txt --no-cache-dir
   ```

### Problem: Node.js Dependencies Installation Fails

**Error Messages:**
```
npm ERR! peer dep missing: react@^18.0.0
npm ERR! ERESOLVE unable to resolve dependency tree
gyp ERR! stack Error: not found: make
```

**Solutions:**
1. **Check Node.js Version**:
   ```bash
   node --version  # Should be 16.0 or higher
   npm --version   # Should be 8.0 or higher
   ```

2. **Clear npm cache**:
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Install with legacy peer deps (if needed)**:
   ```bash
   npm install --legacy-peer-deps
   ```

4. **For Windows build tools issues**:
   ```bash
   npm install --global windows-build-tools
   ```

### Problem: Environment Variables Not Loading

**Error Messages:**
```
ValueError: XAI_API_KEY and GROK_API_URL must be set in environment
KeyError: 'DATABASE_URL'
Configuration error: Missing required environment variables
```

**Solutions:**
1. **Check .env file exists and is properly formatted**:
   ```bash
   # backend/.env should contain:
   XAI_API_KEY=your_xai_api_key_here
   GROK_API_URL=https://api.x.ai/v1
   DATABASE_URL=sqlite:///mindcoach.db
   FLASK_ENV=development
   SECRET_KEY=your_secret_key_here
   ```

2. **Verify .env file location**:
   - Backend .env should be in `backend/.env`
   - Frontend .env should be in `frontend/.env`

3. **Check file permissions**:
   ```bash
   chmod 644 backend/.env
   ```

4. **Restart application after .env changes**:
   ```bash
   # Stop all running processes and restart
   ```

### Problem: Database Initialization Fails

**Error Messages:**
```
sqlite3.OperationalError: no such table: users
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table
Database connection failed
```

**Solutions:**
1. **Run database initialization**:
   ```bash
   cd backend
   python init_db.py
   ```

2. **Check database file permissions**:
   ```bash
   ls -la instance/
   chmod 664 instance/mindcoach.db
   ```

3. **Reset database if corrupted**:
   ```bash
   rm instance/mindcoach.db
   python init_db.py
   ```

4. **Run migrations**:
   ```bash
   python migrate.py
   ```

## Authentication and User Management

### Problem: User Creation Fails

**Error Messages:**
```
409 Conflict: User ID already exists
422 Unprocessable Entity: Invalid email format
500 Internal Server Error: Database constraint violation
```

**Solutions:**
1. **For duplicate user ID**:
   - Choose a different, unique user ID
   - Check if user already exists: `GET /api/users/{user_id}`

2. **For invalid email format**:
   - Ensure email follows standard format: `user@domain.com`
   - Remove special characters except @ and .

3. **For database errors**:
   - Check database connectivity
   - Verify user table exists and has correct schema
   - Check disk space for SQLite database

### Problem: User Authentication Issues

**Error Messages:**
```
401 Unauthorized: User-ID header missing
403 Forbidden: Invalid user credentials
User not found in database
```

**Solutions:**
1. **Ensure User-ID header is included**:
   ```javascript
   fetch('/api/endpoint', {
     headers: {
       'User-ID': 'your_user_id',
       'Content-Type': 'application/json'
     }
   });
   ```

2. **Verify user exists in database**:
   ```bash
   # Check user exists
   curl -X GET http://localhost:5000/api/users/your_user_id
   ```

3. **Create user if doesn't exist**:
   ```bash
   curl -X POST http://localhost:5000/api/users \
     -H "Content-Type: application/json" \
     -d '{"user_id": "your_user_id", "email": "your@email.com"}'
   ```

## Subject Selection Problems

### Problem: Subjects Not Loading

**Error Messages:**
```
Failed to fetch subjects
Network error: ERR_CONNECTION_REFUSED
Subjects list is empty
```

**Solutions:**
1. **Check backend server is running**:
   ```bash
   curl http://localhost:5000/api/subjects
   ```

2. **Verify API endpoint**:
   - Ensure backend is running on correct port (5000)
   - Check CORS configuration allows frontend domain

3. **Check network connectivity**:
   - Disable VPN or proxy temporarily
   - Check firewall settings

4. **Clear browser cache**:
   - Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
   - Clear browser cache and cookies

### Problem: Subject Selection Not Persisting

**Error Messages:**
```
Failed to save subject selection
File system error: Permission denied
Selection.json not found
```

**Solutions:**
1. **Check file system permissions**:
   ```bash
   # Ensure backend can write to users directory
   chmod 755 users/
   ```

2. **Verify user directory structure**:
   ```bash
   # Should create: users/{user_id}/selection.json
   ls -la users/your_user_id/
   ```

3. **Check disk space**:
   ```bash
   df -h  # Ensure sufficient disk space
   ```

4. **Restart backend service**:
   ```bash
   # Stop and restart Flask application
   ```

### Problem: Subscription Status Not Updating

**Error Messages:**
```
Subject appears locked despite active subscription
Subscription check failed
Database query timeout
```

**Solutions:**
1. **Refresh subscription status**:
   ```bash
   curl -X GET http://localhost:5000/api/users/{user_id}/subjects/{subject}/status
   ```

2. **Check database subscription record**:
   ```sql
   SELECT * FROM subscriptions WHERE user_id = 'your_user_id' AND subject = 'subject_name';
   ```

3. **Clear application cache**:
   - Refresh browser page
   - Clear localStorage: `localStorage.clear()`

4. **Verify subscription expiration**:
   - Check `expires_at` field in subscription record
   - Renew subscription if expired

## Survey Generation and Submission Issues

### Problem: Survey Generation Fails

**Error Messages:**
```
xAI API connection failed
LangChain pipeline error: Invalid API key
Survey generation timeout after 60 seconds
Rate limit exceeded for survey generation
```

**Solutions:**
1. **Check xAI API credentials**:
   ```bash
   # Verify environment variables
   echo $XAI_API_KEY
   echo $GROK_API_URL
   ```

2. **Test API connectivity**:
   ```bash
   curl -H "Authorization: Bearer $XAI_API_KEY" \
        -H "Content-Type: application/json" \
        $GROK_API_URL/models
   ```

3. **Check rate limits**:
   - Wait 1 hour before retrying
   - Upgrade API plan if needed
   - Check API usage dashboard

4. **Verify LangChain configuration**:
   ```python
   # Test LangChain setup
   from langchain_community.llms import ChatGroq
   llm = ChatGroq(model="grok-3-mini", api_key="your_key")
   ```

### Problem: Survey Questions Not Displaying

**Error Messages:**
```
Survey data malformed
JSON parse error in survey.json
Questions array is empty
```

**Solutions:**
1. **Check survey.json file format**:
   ```bash
   cat users/{user_id}/{subject}/survey.json | python -m json.tool
   ```

2. **Validate JSON structure**:
   ```json
   {
     "questions": [
       {
         "id": 1,
         "question": "Question text",
         "type": "multiple_choice",
         "options": ["A", "B", "C", "D"]
       }
     ]
   }
   ```

3. **Regenerate survey**:
   ```bash
   curl -X POST http://localhost:5000/api/users/{user_id}/subjects/{subject}/survey/generate
   ```

4. **Check file permissions**:
   ```bash
   chmod 644 users/{user_id}/{subject}/survey.json
   ```

### Problem: Survey Submission Fails

**Error Messages:**
```
Validation error: Missing required answers
Survey submission timeout
Failed to save survey answers
```

**Solutions:**
1. **Ensure all required questions are answered**:
   - Check for red error indicators
   - Scroll through entire survey

2. **Check answer format**:
   ```json
   {
     "survey_id": "survey_12345",
     "answers": [
       {
         "question_id": 1,
         "answer": "selected_option"
       }
     ]
   }
   ```

3. **Retry submission**:
   - Wait a few seconds and try again
   - Check network connection

4. **Clear form and restart**:
   - Refresh page and retake survey
   - Check browser console for JavaScript errors

## Content Generation Pipeline Problems

### Problem: Content Generation Stuck

**Error Messages:**
```
Pipeline timeout: Stage 1 not completing
LangChain chain execution failed
Content generation task expired
Worker process crashed during generation
```

**Solutions:**
1. **Check pipeline status**:
   ```bash
   curl -X GET http://localhost:5000/api/users/{user_id}/subjects/{subject}/content/status/{task_id}
   ```

2. **Monitor task queue**:
   ```bash
   # Check Redis/Celery queue status
   celery -A app.celery inspect active
   ```

3. **Restart content generation**:
   ```bash
   curl -X POST http://localhost:5000/api/users/{user_id}/subjects/{subject}/content/generate
   ```

4. **Check worker processes**:
   ```bash
   # Restart Celery workers
   celery -A app.celery worker --loglevel=info
   ```

### Problem: Generated Content Quality Issues

**Error Messages:**
```
RAG document loading failed
Content validation error: Missing required sections
Generated lesson too short/long
```

**Solutions:**
1. **Check RAG documents**:
   ```bash
   ls -la rag_docs/
   # Ensure all required RAG files exist
   ```

2. **Validate RAG document format**:
   - Check markdown syntax
   - Verify content guidelines structure

3. **Regenerate with different parameters**:
   - Retake survey with more accurate answers
   - Adjust skill level assessment

4. **Check content generation logs**:
   ```bash
   tail -f logs/content_generation.log
   ```

### Problem: Lesson Files Not Created

**Error Messages:**
```
File system error: Cannot create lesson files
Permission denied: users/{user_id}/{subject}/
Lesson content empty or malformed
```

**Solutions:**
1. **Check directory permissions**:
   ```bash
   chmod -R 755 users/
   chown -R app:app users/
   ```

2. **Verify disk space**:
   ```bash
   df -h
   # Ensure sufficient space for lesson files
   ```

3. **Check file creation process**:
   ```bash
   ls -la users/{user_id}/{subject}/
   # Should see lesson_1.md through lesson_10.md
   ```

4. **Manual file creation test**:
   ```bash
   touch users/{user_id}/{subject}/test.md
   # If this fails, check permissions
   ```

## Lesson Access and Display Issues

### Problem: Lessons Not Loading

**Error Messages:**
```
404 Not Found: Lesson file does not exist
Failed to render markdown content
Lesson content is empty
```

**Solutions:**
1. **Verify lesson files exist**:
   ```bash
   ls -la users/{user_id}/{subject}/lesson_*.md
   ```

2. **Check file content**:
   ```bash
   head -20 users/{user_id}/{subject}/lesson_1.md
   ```

3. **Test markdown rendering**:
   - Check browser console for JavaScript errors
   - Verify markdown parser is loaded

4. **Regenerate lessons if missing**:
   ```bash
   curl -X POST http://localhost:5000/api/users/{user_id}/subjects/{subject}/content/generate
   ```

### Problem: Code Syntax Highlighting Not Working

**Error Messages:**
```
Prism.js failed to load
Syntax highlighter initialization error
Code blocks not styled
```

**Solutions:**
1. **Check JavaScript console**:
   - Look for Prism.js or highlight.js errors
   - Verify CDN resources are loading

2. **Test with different browser**:
   - Disable ad blockers
   - Try incognito mode

3. **Check code block format**:
   ```markdown
   ```python
   def example():
       return "Hello World"
   ```
   ```

4. **Reload syntax highlighter**:
   ```javascript
   // In browser console
   Prism.highlightAll();
   ```

### Problem: Lesson Progress Not Saving

**Error Messages:**
```
Progress update failed
Database write error
Session expired
```

**Solutions:**
1. **Check user authentication**:
   - Verify User-ID header is present
   - Ensure session is active

2. **Test progress endpoint**:
   ```bash
   curl -X PUT http://localhost:5000/api/users/{user_id}/subjects/{subject}/lessons/{lesson_id}/progress \
     -H "Content-Type: application/json" \
     -d '{"completion_percentage": 50}'
   ```

3. **Check database connectivity**:
   ```bash
   # Test database connection
   python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
   ```

4. **Clear browser storage**:
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   ```

## Subscription and Payment Problems

### Problem: Payment Processing Fails

**Error Messages:**
```
Payment gateway timeout
Invalid payment token
Credit card declined
Subscription activation failed
```

**Solutions:**
1. **Check payment gateway status**:
   - Verify payment service is operational
   - Check API credentials

2. **Validate payment information**:
   - Ensure card details are correct
   - Check card expiration date
   - Verify billing address

3. **Test with different payment method**:
   - Try different credit card
   - Use PayPal if available

4. **Contact payment support**:
   - Check payment gateway logs
   - Contact merchant support

### Problem: Subscription Not Activating

**Error Messages:**
```
Subscription status not updated
Database transaction failed
Payment successful but access denied
```

**Solutions:**
1. **Check subscription record**:
   ```sql
   SELECT * FROM subscriptions WHERE user_id = 'your_user_id';
   ```

2. **Manually activate subscription**:
   ```sql
   UPDATE subscriptions 
   SET status = 'active', expires_at = DATE('now', '+30 days')
   WHERE user_id = 'your_user_id' AND subject = 'subject_name';
   ```

3. **Refresh application**:
   - Clear browser cache
   - Restart application

4. **Check payment confirmation**:
   - Verify payment was processed
   - Check email confirmation

### Problem: Subscription Expiration Issues

**Error Messages:**
```
Subscription expired but still showing active
Grace period calculation error
Auto-renewal failed
```

**Solutions:**
1. **Check expiration date**:
   ```sql
   SELECT expires_at FROM subscriptions WHERE user_id = 'your_user_id';
   ```

2. **Update expiration manually**:
   ```sql
   UPDATE subscriptions 
   SET expires_at = DATE('now', '+30 days')
   WHERE user_id = 'your_user_id';
   ```

3. **Check auto-renewal settings**:
   - Verify payment method is valid
   - Check auto-renewal configuration

4. **Contact billing support**:
   - Review billing history
   - Check for failed payment attempts

## Performance and Loading Issues

### Problem: Slow Page Loading

**Error Messages:**
```
Page load timeout
Resource loading failed
Network request timeout
```

**Solutions:**
1. **Check network connection**:
   ```bash
   ping google.com
   speedtest-cli
   ```

2. **Optimize browser performance**:
   - Close unnecessary tabs
   - Clear browser cache
   - Disable extensions temporarily

3. **Check server performance**:
   ```bash
   # Monitor server resources
   top
   htop
   df -h
   ```

4. **Enable compression**:
   - Check if gzip is enabled
   - Optimize image sizes
   - Minify CSS/JavaScript

### Problem: High Memory Usage

**Error Messages:**
```
Out of memory error
Browser tab crashed
Application not responding
```

**Solutions:**
1. **Check memory usage**:
   ```bash
   # Server memory
   free -h
   # Browser memory (F12 > Performance)
   ```

2. **Optimize application**:
   - Close unused browser tabs
   - Restart browser
   - Restart application server

3. **Check for memory leaks**:
   - Monitor memory usage over time
   - Check browser developer tools

4. **Increase system resources**:
   - Add more RAM if possible
   - Close other applications

### Problem: Database Performance Issues

**Error Messages:**
```
Database query timeout
SQLite database locked
Connection pool exhausted
```

**Solutions:**
1. **Check database size**:
   ```bash
   ls -lh instance/mindcoach.db
   ```

2. **Optimize database**:
   ```sql
   VACUUM;
   ANALYZE;
   ```

3. **Check for long-running queries**:
   ```sql
   .timeout 30000  -- Set 30 second timeout
   ```

4. **Restart database connection**:
   ```bash
   # Restart Flask application
   ```

## Mobile and Responsive Design Issues

### Problem: Layout Broken on Mobile

**Error Messages:**
```
Viewport meta tag missing
CSS media queries not working
Touch targets too small
```

**Solutions:**
1. **Check viewport meta tag**:
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```

2. **Test responsive breakpoints**:
   - Desktop: 1024px+
   - Tablet: 768px-1023px
   - Mobile: <768px

3. **Check CSS media queries**:
   ```css
   @media (max-width: 767px) {
     /* Mobile styles */
   }
   ```

4. **Test on different devices**:
   - Use browser developer tools
   - Test on actual mobile devices

### Problem: Touch Interactions Not Working

**Error Messages:**
```
Touch events not registered
Buttons not responding to touch
Scroll not working on mobile
```

**Solutions:**
1. **Check touch event handlers**:
   ```javascript
   element.addEventListener('touchstart', handler);
   element.addEventListener('click', handler);
   ```

2. **Verify touch target sizes**:
   - Minimum 44px x 44px for touch targets
   - Add padding around small elements

3. **Test touch scrolling**:
   ```css
   -webkit-overflow-scrolling: touch;
   overflow-y: scroll;
   ```

4. **Check for JavaScript errors**:
   - Open mobile browser console
   - Look for touch-related errors

### Problem: Text Too Small on Mobile

**Error Messages:**
```
Text not readable on mobile
Font size too small
Zoom required to read content
```

**Solutions:**
1. **Check base font size**:
   ```css
   html {
     font-size: 16px; /* Minimum for mobile */
   }
   ```

2. **Use relative units**:
   ```css
   .text {
     font-size: 1rem; /* 16px */
     line-height: 1.5;
   }
   ```

3. **Test readability**:
   - Use browser zoom to test
   - Check contrast ratios

4. **Implement responsive typography**:
   ```css
   @media (max-width: 767px) {
     body {
       font-size: 18px;
     }
   }
   ```

## API Integration Problems

### Problem: CORS Errors

**Error Messages:**
```
Access to fetch blocked by CORS policy
No 'Access-Control-Allow-Origin' header
Preflight request failed
```

**Solutions:**
1. **Configure CORS in Flask**:
   ```python
   from flask_cors import CORS
   CORS(app, origins=['http://localhost:3000'])
   ```

2. **Check allowed origins**:
   ```python
   CORS(app, origins=['*'])  # For development only
   ```

3. **Verify request headers**:
   ```javascript
   fetch('/api/endpoint', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'User-ID': 'user123'
     }
   });
   ```

4. **Test with curl**:
   ```bash
   curl -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS http://localhost:5000/api/users
   ```

### Problem: API Rate Limiting

**Error Messages:**
```
429 Too Many Requests
Rate limit exceeded
API quota exhausted
```

**Solutions:**
1. **Check rate limit headers**:
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 0
   X-RateLimit-Reset: 1642262400
   ```

2. **Implement retry logic**:
   ```javascript
   const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
   
   async function apiCallWithRetry(url, options, maxRetries = 3) {
     for (let i = 0; i < maxRetries; i++) {
       const response = await fetch(url, options);
       if (response.status !== 429) return response;
       await delay(1000 * Math.pow(2, i)); // Exponential backoff
     }
   }
   ```

3. **Optimize API usage**:
   - Cache responses when possible
   - Batch multiple requests
   - Reduce polling frequency

4. **Upgrade API plan**:
   - Check current usage limits
   - Contact API provider for higher limits

### Problem: API Response Validation Errors

**Error Messages:**
```
JSON schema validation failed
Required field missing in response
Invalid data type in API response
```

**Solutions:**
1. **Check API response format**:
   ```bash
   curl -X GET http://localhost:5000/api/users/test_user | python -m json.tool
   ```

2. **Validate response schema**:
   ```javascript
   // Check required fields exist
   if (!response.data || !response.data.user_id) {
     throw new Error('Invalid API response');
   }
   ```

3. **Handle API errors gracefully**:
   ```javascript
   try {
     const response = await fetch('/api/endpoint');
     if (!response.ok) {
       throw new Error(`API error: ${response.status}`);
     }
     const data = await response.json();
   } catch (error) {
     console.error('API call failed:', error);
   }
   ```

4. **Check API version compatibility**:
   - Verify using correct API version
   - Check for breaking changes

## Docker and Deployment Issues

### Problem: Docker Container Won't Start

**Error Messages:**
```
Container exited with code 1
Port already in use
Docker daemon not running
Image build failed
```

**Solutions:**
1. **Check Docker daemon**:
   ```bash
   docker --version
   systemctl status docker
   ```

2. **Check port conflicts**:
   ```bash
   netstat -tulpn | grep :5000
   lsof -i :5000
   ```

3. **View container logs**:
   ```bash
   docker logs container_name
   docker logs --tail 50 container_name
   ```

4. **Rebuild container**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

### Problem: Docker Volume Mount Issues

**Error Messages:**
```
Volume mount failed
Permission denied in container
File not found in mounted volume
```

**Solutions:**
1. **Check volume permissions**:
   ```bash
   ls -la /path/to/volume
   chmod 755 /path/to/volume
   ```

2. **Fix ownership issues**:
   ```bash
   sudo chown -R 1000:1000 /path/to/volume
   ```

3. **Verify mount paths**:
   ```yaml
   # docker-compose.yml
   volumes:
     - ./backend:/app
     - ./data:/app/data
   ```

4. **Test volume mounting**:
   ```bash
   docker run -v $(pwd):/test alpine ls -la /test
   ```

### Problem: Container Networking Issues

**Error Messages:**
```
Connection refused between containers
Service discovery failed
Network not found
```

**Solutions:**
1. **Check Docker networks**:
   ```bash
   docker network ls
   docker network inspect bridge
   ```

2. **Test container connectivity**:
   ```bash
   docker exec container1 ping container2
   ```

3. **Check service names in docker-compose**:
   ```yaml
   services:
     backend:
       # Other containers can reach this as 'backend'
     frontend:
       # Can connect to backend using 'http://backend:5000'
   ```

4. **Restart Docker networking**:
   ```bash
   docker-compose down
   docker network prune
   docker-compose up
   ```

## Database and File System Issues

### Problem: SQLite Database Corruption

**Error Messages:**
```
sqlite3.DatabaseError: database disk image is malformed
Database is locked
Disk I/O error
```

**Solutions:**
1. **Check database integrity**:
   ```bash
   sqlite3 instance/mindcoach.db "PRAGMA integrity_check;"
   ```

2. **Backup and restore database**:
   ```bash
   sqlite3 instance/mindcoach.db ".backup backup.db"
   rm instance/mindcoach.db
   sqlite3 instance/mindcoach.db ".restore backup.db"
   ```

3. **Recreate database**:
   ```bash
   rm instance/mindcoach.db
   python init_db.py
   ```

4. **Check disk space and permissions**:
   ```bash
   df -h
   ls -la instance/
   ```

### Problem: File System Permission Errors

**Error Messages:**
```
Permission denied: users/user123/python/
Cannot create directory
File write failed
```

**Solutions:**
1. **Fix directory permissions**:
   ```bash
   chmod -R 755 users/
   chown -R $USER:$USER users/
   ```

2. **Check parent directory permissions**:
   ```bash
   ls -la users/
   mkdir -p users/test_user/test_subject
   ```

3. **Verify disk space**:
   ```bash
   df -h
   du -sh users/
   ```

4. **Check SELinux/AppArmor**:
   ```bash
   # Disable temporarily for testing
   sudo setenforce 0
   ```

### Problem: File Encoding Issues

**Error Messages:**
```
UnicodeDecodeError: 'utf-8' codec can't decode
Invalid character in file
Encoding detection failed
```

**Solutions:**
1. **Check file encoding**:
   ```bash
   file -i users/user123/python/lesson_1.md
   ```

2. **Convert file encoding**:
   ```bash
   iconv -f ISO-8859-1 -t UTF-8 input.md > output.md
   ```

3. **Set proper encoding in Python**:
   ```python
   with open('file.md', 'r', encoding='utf-8') as f:
       content = f.read()
   ```

4. **Check for BOM (Byte Order Mark)**:
   ```bash
   hexdump -C file.md | head -1
   # Look for EF BB BF at start
   ```

## Getting Additional Help

If you continue experiencing issues after trying these solutions:

### 1. Check System Status
- Visit our status page: `https://status.mindcoach.com`
- Check for known issues and maintenance windows

### 2. Gather Diagnostic Information
Before contacting support, collect:
- Error messages (exact text)
- Browser/system information
- Steps to reproduce the issue
- Screenshots if applicable

### 3. Log Files to Check
- Backend logs: `backend/logs/app.log`
- Content generation logs: `backend/logs/content_generation.log`
- Browser console errors (F12 > Console)
- Docker container logs: `docker logs container_name`

### 4. Contact Support Channels
- **Email Support**: support@mindcoach.com
- **Community Forum**: https://community.mindcoach.com
- **GitHub Issues**: https://github.com/mindcoach/issues
- **Live Chat**: Available during business hours

### 5. Emergency Contacts
For critical production issues:
- **Emergency Hotline**: +1-555-MINDCOACH
- **Slack Channel**: #mindcoach-emergency
- **On-call Engineer**: emergency@mindcoach.com

## Preventive Measures

### Regular Maintenance
1. **Update Dependencies**:
   ```bash
   pip list --outdated
   npm audit
   ```

2. **Database Maintenance**:
   ```sql
   VACUUM;
   ANALYZE;
   PRAGMA integrity_check;
   ```

3. **Log Rotation**:
   ```bash
   # Set up logrotate for application logs
   ```

4. **Backup Strategy**:
   ```bash
   # Regular database backups
   sqlite3 instance/mindcoach.db ".backup backup_$(date +%Y%m%d).db"
   ```

### Monitoring Setup
1. **Health Checks**:
   ```bash
   curl http://localhost:5000/health
   ```

2. **Resource Monitoring**:
   ```bash
   # Monitor disk space, memory, CPU
   ```

3. **Error Tracking**:
   - Set up error logging
   - Monitor error rates
   - Alert on critical errors

### Best Practices
1. **Development Environment**:
   - Use virtual environments
   - Keep dependencies updated
   - Test in staging before production

2. **Production Deployment**:
   - Use Docker containers
   - Implement proper logging
   - Set up monitoring and alerts

3. **User Experience**:
   - Test on multiple devices
   - Monitor performance metrics
   - Gather user feedback regularly