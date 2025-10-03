# Reddit Dashboard - GitHub Pages

This folder contains the deployed dashboard files for GitHub Pages.

## Deployment Method

This dashboard is deployed using **GitHub Actions** instead of static branch deployment for the following benefits:

### ✅ **GitHub Actions Deployment Advantages:**

1. **🔄 Automatic Updates**: Dashboard deploys automatically when new data is fetched
2. **📊 Real-time Sync**: Data and dashboard stay in sync
3. **🚀 Better Control**: Can run build steps, optimizations, and validations
4. **📈 Scalability**: Can handle complex deployment logic
5. **🔧 Customization**: Can add pre-processing, compression, etc.

### 🔄 **How It Works:**

1. **Reddit Monitor Workflow** runs every 4 hours
2. **Fetches new data** and commits to repository
3. **Deploy Dashboard Workflow** triggers automatically
4. **Copies dashboard files** to docs folder
5. **Deploys to GitHub Pages** with latest data

### 📁 **File Structure:**

- `index.html` - Main dashboard page
- `css/styles.css` - Dashboard styling
- `js/dashboard.js` - Main dashboard logic
- `js/utils.js` - Utility functions
- `data.json` - Latest Reddit data (auto-updated)

### 🚀 **Live Dashboard:**

Visit: https://nimishpande.github.io/Reddit-Dash/

---

**Note**: This folder is automatically managed by GitHub Actions. Manual changes will be overwritten on the next deployment.
# Updated Fri Oct  3 20:05:41 IST 2025
