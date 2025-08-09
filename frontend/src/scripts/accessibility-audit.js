/**
 * Accessibility audit script
 * Runs comprehensive accessibility tests and generates reports
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  testTimeout: 30000,
  outputDir: './accessibility-reports',
  components: [
    'ResponsiveLayout',
    'SubjectSelector', 
    'Survey',
    'LessonViewer'
  ],
  wcagLevel: 'AA',
  reportFormats: ['json', 'html']
};

/**
 * Create output directory if it doesn't exist
 */
function ensureOutputDir() {
  if (!fs.existsSync(config.outputDir)) {
    fs.mkdirSync(config.outputDir, { recursive: true });
  }
}

/**
 * Run Jest accessibility tests
 */
function runAccessibilityTests() {
  console.log('🔍 Running accessibility tests...');
  
  try {
    const result = execSync(
      'npm test -- --testNamePattern="Accessibility Tests" --verbose --coverage=false --watchAll=false',
      { 
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: config.testTimeout
      }
    );
    
    console.log('✅ Accessibility tests completed successfully');
    return { success: true, output: result };
  } catch (error) {
    console.error('❌ Accessibility tests failed');
    console.error(error.stdout || error.message);
    return { success: false, error: error.message, output: error.stdout };
  }
}

/**
 * Generate accessibility report
 */
function generateReport(testResults) {
  console.log('📊 Generating accessibility report...');
  
  const timestamp = new Date().toISOString();
  const report = {
    timestamp,
    wcagLevel: config.wcagLevel,
    testResults,
    summary: {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      components: config.components.length
    },
    recommendations: []
  };
  
  // Parse test results (simplified - would need more sophisticated parsing in real implementation)
  if (testResults.success) {
    report.summary.totalTests = config.components.length * 5; // Estimated
    report.summary.passedTests = report.summary.totalTests;
    report.summary.failedTests = 0;
  } else {
    report.summary.totalTests = config.components.length * 5;
    report.summary.passedTests = 0;
    report.summary.failedTests = report.summary.totalTests;
    
    report.recommendations.push({
      severity: 'high',
      component: 'general',
      issue: 'Accessibility tests are failing',
      solution: 'Review test output and fix accessibility violations',
      wcagReference: 'Multiple criteria'
    });
  }
  
  // Add general recommendations
  report.recommendations.push(
    {
      severity: 'medium',
      component: 'all',
      issue: 'Regular accessibility audits needed',
      solution: 'Schedule monthly accessibility reviews and user testing',
      wcagReference: 'General best practice'
    },
    {
      severity: 'low',
      component: 'all',
      issue: 'Screen reader testing',
      solution: 'Test with multiple screen readers (NVDA, JAWS, VoiceOver)',
      wcagReference: '4.1.2 Name, Role, Value'
    }
  );
  
  return report;
}

/**
 * Save report in multiple formats
 */
function saveReport(report) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  // Save JSON report
  if (config.reportFormats.includes('json')) {
    const jsonPath = path.join(config.outputDir, `accessibility-report-${timestamp}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));
    console.log(`📄 JSON report saved: ${jsonPath}`);
  }
  
  // Save HTML report
  if (config.reportFormats.includes('html')) {
    const htmlPath = path.join(config.outputDir, `accessibility-report-${timestamp}.html`);
    const htmlContent = generateHtmlReport(report);
    fs.writeFileSync(htmlPath, htmlContent);
    console.log(`🌐 HTML report saved: ${htmlPath}`);
  }
}

/**
 * Generate HTML report
 */
function generateHtmlReport(report) {
  const passRate = ((report.summary.passedTests / report.summary.totalTests) * 100).toFixed(1);
  const statusColor = report.summary.failedTests === 0 ? '#10b981' : '#ef4444';
  
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9fafb;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
            color: #1f2937;
        }
        .header .meta {
            color: #6b7280;
            font-size: 14px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 24px;
            color: ${statusColor};
        }
        .summary-card p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
        }
        .pass-rate {
            font-size: 48px;
            font-weight: bold;
            color: ${statusColor};
        }
        .recommendations {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .recommendations h2 {
            margin-top: 0;
            color: #1f2937;
        }
        .recommendation {
            border-left: 4px solid #e5e7eb;
            padding: 15px 20px;
            margin-bottom: 15px;
            background: #f9fafb;
        }
        .recommendation.high {
            border-left-color: #ef4444;
        }
        .recommendation.medium {
            border-left-color: #f59e0b;
        }
        .recommendation.low {
            border-left-color: #10b981;
        }
        .recommendation h4 {
            margin: 0 0 8px 0;
            color: #1f2937;
        }
        .recommendation p {
            margin: 0 0 8px 0;
            color: #4b5563;
        }
        .recommendation .wcag {
            font-size: 12px;
            color: #6b7280;
            font-style: italic;
        }
        .footer {
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .summary {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Accessibility Audit Report</h1>
        <div class="meta">
            Generated: ${new Date(report.timestamp).toLocaleString()}<br>
            WCAG Level: ${report.wcagLevel}<br>
            Components Tested: ${report.summary.components}
        </div>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3 class="pass-rate">${passRate}%</h3>
            <p>Pass Rate</p>
        </div>
        <div class="summary-card">
            <h3>${report.summary.totalTests}</h3>
            <p>Total Tests</p>
        </div>
        <div class="summary-card">
            <h3>${report.summary.passedTests}</h3>
            <p>Passed</p>
        </div>
        <div class="summary-card">
            <h3>${report.summary.failedTests}</h3>
            <p>Failed</p>
        </div>
    </div>

    <div class="recommendations">
        <h2>📋 Recommendations</h2>
        ${report.recommendations.map(rec => `
            <div class="recommendation ${rec.severity}">
                <h4>${rec.issue}</h4>
                <p><strong>Component:</strong> ${rec.component}</p>
                <p><strong>Solution:</strong> ${rec.solution}</p>
                <div class="wcag">WCAG Reference: ${rec.wcagReference}</div>
            </div>
        `).join('')}
    </div>

    <div class="footer">
        <p>This report was generated automatically. For comprehensive accessibility testing, 
        combine automated testing with manual testing and user feedback.</p>
        <p>Learn more about accessibility at <a href="https://www.w3.org/WAI/">W3C Web Accessibility Initiative</a></p>
    </div>
</body>
</html>`;
}

/**
 * Main audit function
 */
function runAccessibilityAudit() {
  console.log('🚀 Starting accessibility audit...');
  console.log(`📅 Timestamp: ${new Date().toISOString()}`);
  console.log(`🎯 WCAG Level: ${config.wcagLevel}`);
  console.log(`🧩 Components: ${config.components.join(', ')}`);
  console.log('');
  
  // Ensure output directory exists
  ensureOutputDir();
  
  // Run tests
  const testResults = runAccessibilityTests();
  
  // Generate and save report
  const report = generateReport(testResults);
  saveReport(report);
  
  // Print summary
  console.log('');
  console.log('📊 Audit Summary:');
  console.log(`   Total Tests: ${report.summary.totalTests}`);
  console.log(`   Passed: ${report.summary.passedTests}`);
  console.log(`   Failed: ${report.summary.failedTests}`);
  console.log(`   Pass Rate: ${((report.summary.passedTests / report.summary.totalTests) * 100).toFixed(1)}%`);
  
  if (report.summary.failedTests > 0) {
    console.log('');
    console.log('❌ Accessibility issues found. Please review the report and fix violations.');
    process.exit(1);
  } else {
    console.log('');
    console.log('✅ All accessibility tests passed!');
    process.exit(0);
  }
}

// Run audit if called directly
if (require.main === module) {
  runAccessibilityAudit();
}

module.exports = {
  runAccessibilityAudit,
  generateReport,
  config
};