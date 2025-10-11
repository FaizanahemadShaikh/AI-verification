# Render deployment guide
# This file contains instructions for deploying to Render

## Step 1: Prepare your code
1. Make sure all files are committed to Git
2. Push to GitHub repository

## Step 2: Deploy on Render
1. Go to https://render.com
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure settings (see below)

## Step 3: Render Configuration
- **Name**: waste-verification-api (or your preferred name)
- **Environment**: Python 3
- **Build Command**: pip install -r requirements.txt
- **Start Command**: uvicorn app:app --host 0.0.0.0 --port $PORT
- **Plan**: Free (or paid for better performance)

## Step 4: Environment Variables
Add these in Render dashboard:
- GEMINI_API_KEY: AIzaSyBu9J0OsbOIZTvTp0J4ty6pHE5fdotLXys

## Step 5: Deploy
Click "Create Web Service" and wait for deployment

## Step 6: Test your API
Your API will be available at: https://your-app-name.onrender.com
- Root: https://your-app-name.onrender.com/
- Docs: https://your-app-name.onrender.com/docs
- Analyze URL: https://your-app-name.onrender.com/analyze-image-url/

## Mobile App Integration
Update your Kotlin app to use:
```kotlin
val baseUrl = "https://your-app-name.onrender.com"
val endpoint = "$baseUrl/analyze-image-url/"
```
