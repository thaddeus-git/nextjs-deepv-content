#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function log(color, message) {
  const colors = {
    reset: "\x1b[0m",
    red: "\x1b[31m", 
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    blue: "\x1b[34m",
    cyan: "\x1b[36m"
  };
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function main() {
  log("cyan", "🚀 DeepV Code Content Promotion (Skip Validation)");
  log("cyan", "==================================================");
  console.log("");

  try {
    log("yellow", "⚠️  Skipping validation step - proceeding with promotion...");
    log("blue", "🔄 Step 2: Promoting content to production...");
    
    const stagingDir = "staging/guides";
    const productionDir = "guides";
    const stagingConfig = "staging/config/article-index-update.json";
    const productionConfig = "config/article-index.json";

    if (!fs.existsSync(productionDir)) {
      fs.mkdirSync(productionDir, { recursive: true });
    }

    let promotedCount = 0;

    if (fs.existsSync(stagingDir)) {
      const files = fs.readdirSync(stagingDir).filter(f => f.endsWith(".mdx"));
      
      for (const file of files) {
        const sourcePath = path.join(stagingDir, file);
        const destPath = path.join(productionDir, file);
        
        fs.copyFileSync(sourcePath, destPath);
        fs.unlinkSync(sourcePath);
        log("green", `  ✅ Promoted: ${file}`);
        promotedCount++;
      }
    }

    if (fs.existsSync(stagingConfig)) {
      fs.copyFileSync(stagingConfig, productionConfig);
      fs.unlinkSync(stagingConfig);
      log("green", "  ✅ Updated article index");
    }

    if (promotedCount === 0) {
      log("yellow", "⚠️  No content found in staging. Nothing to promote.");
      return;
    }

    console.log("");
    log("blue", "📤 Step 3: Committing to GitHub...");
    
    execSync("git add .", { stdio: "inherit" });
    
    const date = new Date().toISOString().split("T")[0];
    const commitMsg = `Add ${promotedCount} new articles - ${date}`;
    
    execSync(`git commit -m "${commitMsg}"`, { stdio: "inherit" });
    execSync("git push", { stdio: "inherit" });
    
    console.log("");
    log("green", "🎉 Promotion successful!");
    log("cyan", "Content will appear on https://deepvcode.com within 5 minutes (ISR)");

  } catch (error) {
    console.log("");
    log("red", "❌ Promotion failed: " + error.message);
    process.exit(1);
  }
}

main();