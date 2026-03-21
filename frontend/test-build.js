#!/usr/bin/env node
/**
 * Simple script to test if our React components can be parsed
 */

const fs = require('fs');
const path = require('path');

console.log('Testing frontend code for syntax errors...\n');

const filesToCheck = [
  'src/contexts/AuthContext.jsx',
  'src/components/Navigation.jsx',
  'src/pages/login.jsx',
  'src/pages/signup.jsx',
  'src/pages/dashboard.jsx',
  'src/pages/profile.jsx',
  'src/components/SupportForm.jsx',
  'src/pages/_app.jsx',
  'src/pages/index.jsx',
];

let hasErrors = false;

filesToCheck.forEach(file => {
  const fullPath = path.join(__dirname, file);

  if (!fs.existsSync(fullPath)) {
    console.error(`❌ File not found: ${file}`);
    hasErrors = true;
    return;
  }

  const content = fs.readFileSync(fullPath, 'utf8');

  // Check for common issues
  const issues = [];

  // Check for unclosed tags/brackets
  const openBraces = (content.match(/{/g) || []).length;
  const closeBraces = (content.match(/}/g) || []).length;
  const openParens = (content.match(/\(/g) || []).length;
  const closeParens = (content.match(/\)/g) || []).length;
  const openBrackets = (content.match(/\[/g) || []).length;
  const closeBrackets = (content.match(/\]/g) || []).length;

  if (openBraces !== closeBraces) {
    issues.push(`Unmatched braces: ${openBraces} open, ${closeBraces} close`);
  }
  if (openParens !== closeParens) {
    issues.push(`Unmatched parentheses: ${openParens} open, ${closeParens} close`);
  }
  if (openBrackets !== closeBrackets) {
    issues.push(`Unmatched brackets: ${openBrackets} open, ${closeBrackets} close`);
  }

  // Check for missing imports
  if (content.includes('useAuth') && !content.includes("from '../contexts/AuthContext'") && !content.includes("from './contexts/AuthContext'")) {
    if (!file.includes('AuthContext')) {
      issues.push('Uses useAuth but missing import');
    }
  }

  if (content.includes('useRouter') && !content.includes("from 'next/router'")) {
    issues.push('Uses useRouter but missing import');
  }

  if (issues.length > 0) {
    console.error(`❌ ${file}:`);
    issues.forEach(issue => console.error(`   - ${issue}`));
    hasErrors = true;
  } else {
    console.log(`✅ ${file}`);
  }
});

if (hasErrors) {
  console.log('\n❌ Found issues in some files');
  process.exit(1);
} else {
  console.log('\n✅ All files passed basic syntax checks');
  process.exit(0);
}
