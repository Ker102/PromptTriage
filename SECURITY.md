# Security Policy

## 🔒 Security Overview

The security of PromptTriage is a top priority. We appreciate the efforts of security researchers and users who help us maintain a secure platform. This document outlines our security policy and how to report vulnerabilities responsibly.

## 📋 Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          | Status           |
| ------- | ------------------ | ---------------- |
| 0.1.x   | :white_check_mark: | Current Release  |
| < 0.1   | :x:                | Not Supported    |

**Note**: As the project matures, we will update this table with our version support policy.

## 🐛 Reporting a Vulnerability

**⚠️ IMPORTANT: Please DO NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it responsibly:

### Preferred Method: GitHub Security Advisories

1. Go to the [Security Advisories page](https://github.com/Ker102/PromptTriage/security/advisories)
2. Click "Report a vulnerability"
3. Fill out the form with:
   - Clear description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### Alternative Method: Private Contact

If you prefer not to use GitHub Security Advisories, you can contact the maintainers directly through GitHub. Please include:

- **Subject**: "Security Vulnerability Report: [Brief Description]"
- **Description**: Detailed explanation of the vulnerability
- **Reproduction Steps**: Clear steps to reproduce the issue
- **Impact Assessment**: Your assessment of the severity and potential impact
- **Proof of Concept**: If applicable (please be responsible with sensitive data)
- **Suggested Fix**: If you have recommendations

## 🕐 Response Timeline

We take security seriously and will respond promptly:

- **Initial Response**: Within 48 hours of receiving your report
- **Status Update**: Within 5 business days with our assessment
- **Fix Timeline**: Depends on severity, but critical issues will be prioritized
- **Disclosure**: We will coordinate with you on public disclosure timing

### Severity Levels

| Severity | Response Time | Example                                    |
| -------- | ------------- | ------------------------------------------ |
| Critical | 24-48 hours   | Remote code execution, data breach         |
| High     | 3-5 days      | Authentication bypass, XSS                 |
| Medium   | 7-14 days     | Information disclosure, CSRF               |
| Low      | 14-30 days    | Minor configuration issues                 |

## 🎯 Scope

### In Scope

The following are within the scope of our security policy:

- **Application Security**
  - Cross-Site Scripting (XSS)
  - Cross-Site Request Forgery (CSRF)
  - SQL Injection (if applicable)
  - Authentication and authorization issues
  - Session management vulnerabilities
  - Sensitive data exposure

- **API Security**
  - API authentication and authorization
  - Rate limiting bypass
  - API key exposure
  - Input validation issues

- **Infrastructure**
  - Server-side vulnerabilities
  - Dependency vulnerabilities
  - Configuration issues

- **Third-Party Integrations**
  - Google Gemini API integration security
  - OAuth implementation issues
  - Firecrawl integration vulnerabilities

### Out of Scope

The following are generally not considered security vulnerabilities:

- Denial of Service (DoS) attacks
- Social engineering attacks
- Physical attacks
- Issues in third-party services (report to the service provider)
- Issues requiring physical access to a user's device
- Known issues already reported and being addressed
- Theoretical vulnerabilities without proven exploit

## 🛡️ Security Best Practices

### For Users

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use `.env.local` for sensitive configuration
- **Dependencies**: Keep dependencies up to date
- **Access Control**: Use strong, unique passwords for Google OAuth
- **Network**: Use HTTPS in production environments
- **Updates**: Keep PromptTriage updated to the latest version

### For Contributors

- **Code Review**: All code goes through security-focused review
- **Input Validation**: Validate and sanitize all user inputs
- **Output Encoding**: Encode outputs to prevent XSS
- **Authentication**: Follow secure authentication practices
- **Dependencies**: Vet new dependencies for security issues
- **Secrets**: Never hardcode secrets or API keys
- **Error Handling**: Don't expose sensitive information in error messages

## 🔐 Security Features

### Current Security Measures

- **Authentication**: Google OAuth 2.0 via NextAuth.js
- **API Security**: Server-side API routes with validation
- **Environment Variables**: Secure configuration management
- **Dependencies**: Regular dependency updates via Dependabot
- **Code Scanning**: Automated security scanning with CodeQL

### Planned Security Enhancements

- [ ] Rate limiting for API endpoints
- [ ] Enhanced input sanitization
- [ ] Content Security Policy (CSP) headers
- [ ] Automated security testing in CI/CD
- [ ] Regular security audits

## 📦 Dependencies

### Monitoring

We actively monitor our dependencies for security vulnerabilities:

- **Dependabot**: Automated dependency updates
- **npm audit**: Regular security audits
- **GitHub Security Advisories**: Automatic alerts for known vulnerabilities

### Updating Dependencies

When a security vulnerability is discovered in a dependency:

1. We assess the impact on PromptTriage
2. We test the updated dependency
3. We release a patch as soon as possible
4. We communicate the update to users

## 🚨 Known Security Considerations

### API Key Management

- **Gemini API Key**: Required for core functionality
  - Store in `.env.local` (never commit to Git)
  - Use environment-specific keys (dev vs. production)
  - Rotate keys regularly
  - Monitor usage for anomalies

- **Firecrawl API Key**: Optional, for web enrichment
  - Same security practices as Gemini API key
  - Can be omitted if web enrichment is not needed

### Authentication

- **NextAuth.js**: Handles OAuth flows securely
  - Use strong `NEXTAUTH_SECRET`
  - Configure trusted redirect URLs
  - Implement session timeouts

### Client-Side Security

- **API Calls**: Made through Next.js API routes (server-side)
- **User Input**: Validated before processing
- **Output Rendering**: React's built-in XSS protection

## 📢 Disclosure Policy

### Coordinated Disclosure

We believe in coordinated disclosure:

1. **Report**: You report the vulnerability privately
2. **Acknowledgment**: We acknowledge receipt within 48 hours
3. **Investigation**: We investigate and develop a fix
4. **Notification**: We notify you when the fix is ready
5. **Release**: We release the fix in a security update
6. **Disclosure**: We publicly disclose after users have time to update
7. **Credit**: We credit you (if desired) in release notes and security advisories

### Public Disclosure

- We will coordinate with you on disclosure timing
- Typical disclosure: 90 days after fix is released
- Faster for critical vulnerabilities affecting users
- We respect your preference for attribution

## 🏆 Recognition

We appreciate security researchers who help us maintain a secure platform:

- **Hall of Fame**: Contributors are recognized in our security hall of fame
- **Release Notes**: Security fixes credit the reporter (with permission)
- **Social Media**: We may acknowledge your contribution publicly (with permission)

## 📝 Security Updates

### Notifications

Stay informed about security updates:

- **GitHub Security Advisories**: Subscribe to repository security alerts
- **GitHub Watch**: Watch the repository for releases
- **Release Notes**: Check release notes for security fixes

### Applying Updates

When a security update is released:

1. Review the release notes
2. Update your dependencies: `npm update`
3. Test your installation
4. Deploy to production

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Next.js Security](https://nextjs.org/docs/advanced-features/security-headers)
- [TypeScript Security Best Practices](https://www.typescriptlang.org/docs/handbook/security.html)
- [npm Security Best Practices](https://docs.npmjs.com/security-best-practices)

## ❓ Questions

If you have questions about this security policy:

- Open a [GitHub Discussion](https://github.com/Ker102/PromptTriage/discussions)
- Check our [Contributing Guidelines](CONTRIBUTING.md)
- Review our [Code of Conduct](CODE_OF_CONDUCT.md)

---

**Thank you for helping keep PromptTriage and our users safe!** 🛡️
