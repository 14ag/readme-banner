# Deployment Guide: Random README Banner

You need three accounts: **GitHub**, **Supabase**, and **Vercel**.
No local installs are required to deploy. You only need a browser.

---

## Part 1 — Supabase: Create the Database

### Step 1.1 — Create a new project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click **New project**
3. Give it a name, e.g. `random-banner`
4. Choose a region close to you
5. Set a database password (save it somewhere safe)
6. Click **Create new project** and wait about 60 seconds

### Step 1.2 — Create the tables

1. In your project sidebar click **SQL Editor**
2. Click **New query**
3. Paste the SQL below into the editor
4. Click **Run**

```sql
CREATE TABLE shown_banners (
  id           SERIAL PRIMARY KEY,
  image_number INTEGER NOT NULL CHECK (image_number BETWEEN 1 AND 30),
  shown_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rate_limit (
  id           INTEGER PRIMARY KEY DEFAULT 1,
  image_number INTEGER NOT NULL,
  available_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE shown_banners DISABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit     DISABLE ROW LEVEL SECURITY;
```

5. You should see **Success** in the output panel
6. Go to **Table Editor** in the sidebar and confirm both tables appear

### Step 1.3 — Copy your credentials

1. In the sidebar go to **Project Settings** → **API**
2. Copy and save two values:
   - **Project URL** — looks like `https://abcdefgh.supabase.co`
   - **anon public key** — a long string starting with `eyJ`

You will need both in Part 3.

---

## Part 2 — GitHub: Create and Push the Repository

### Step 2.1 — Create a new repository

1. Go to [https://github.com](https://github.com) and sign in
2. Click the **+** icon at the top right → **New repository**
3. Name it `random-banner`
4. Set it to **Public** (Vercel free tier requires public repos)
5. Do **not** add a README or .gitignore (you will push your own files)
6. Click **Create repository**

### Step 2.2 — Upload your project files

If you have Git installed locally:

```bash
# in your project folder
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/random-banner.git
git push -u origin main
```

If you do not have Git locally, use GitHub's web upload:

1. Open the repository on GitHub
2. Click **Add file** → **Upload files**
3. Drag and drop all your project files and folders
4. Click **Commit changes**

> Make sure `src/img/` with all 30 WebP files is included.
> Make sure `.env` is **not** uploaded. It should be in your `.gitignore`.

### Step 2.3 — Save your Banner Key as a GitHub Secret

This is optional but good practice if you ever use GitHub Actions.

1. In your repository go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `BANNER_KEY`
4. Value: the unique key you invented (any random string you choose)
5. Click **Add secret**

---

## Part 3 — Vercel: Deploy the Backend

### Step 3.1 — Import the project

1. Go to [https://vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Under **Import Git Repository** find your `random-banner` repo
4. Click **Import**

### Step 3.2 — Configure the project

On the configuration screen:

- **Framework Preset**: select **Other** (not Next.js)
- **Root Directory**: leave it as `/` (the project root)
- **Build Command**: leave it empty
- **Output Directory**: leave it empty

Vercel detects FastAPI automatically from `requirements.txt`.

### Step 3.3 — Add environment variables

Still on the configuration screen, scroll to **Environment Variables**.

Add these three variables one by one:

| Name          | Value                                      |
|---------------|--------------------------------------------|
| SUPABASE_URL  | your Project URL from Step 1.3             |
| SUPABASE_KEY  | your anon public key from Step 1.3         |
| BANNER_KEY    | the same unique key you set in Step 2.3    |

Click **Add** after each one.

### Step 3.4 — Deploy

Click **Deploy**.

Vercel will:
- Clone your repository
- Install the packages from `requirements.txt`
- Deploy the FastAPI app as a serverless function

This takes about 60 to 90 seconds.

When finished you will see **Congratulations!** and a live URL like:
`https://random-banner-abc123.vercel.app`

---

## Part 4 — Add the Banner to Your README

### Step 4.1 — Get your banner URL

Your banner URL follows this pattern:

```
https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=YOUR_BANNER_KEY
```

Replace:
- `YOUR_VERCEL_DOMAIN` with your actual Vercel project domain
- `YOUR_BANNER_KEY` with the same key you set as `BANNER_KEY`

### Step 4.2 — Add it to any README

Open the target repository's `README.md` and add this line at the very top:

```markdown
![Banner](https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=YOUR_BANNER_KEY)
```

Commit and push. The banner will appear at the top of the README on GitHub.

> **Note about image refresh speed:**
> GitHub caches README images for a few minutes through its image proxy (camo.githubusercontent.com).
> This is normal. The image will update the next time GitHub refreshes its cache.
> The rotation logic works correctly on the backend regardless of GitHub's cache.

---

## Part 5 — Verify Everything Works

### Step 5.1 — Test the health endpoint

Open this URL in your browser:

```
https://YOUR_VERCEL_DOMAIN.vercel.app/health
```

You should see:

```json
{"status": "ok"}
```

### Step 5.2 — Test the banner endpoint

Open this URL in your browser (replace the values):

```
https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=YOUR_BANNER_KEY
```

You should see a WebP image displayed in your browser.

### Step 5.3 — Test key rejection

Open the same URL but with a wrong key:

```
https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=wrongkey
```

You should see `403 Forbidden`.

### Step 5.4 — Check Supabase after the first request

1. Go to Supabase → **Table Editor** → `shown_banners`
2. You should see one row with an `image_number` between 1 and 30
3. Go to `rate_limit` → you should see one row with `id = 1`

If all of the above pass, the system is working correctly.

---

## Part 6 — Future Updates

### To update the backend code

1. Edit the file locally and push to GitHub
2. Vercel automatically redeploys on every push to `main`
3. No manual action needed

### To change the BANNER_KEY

1. Go to Vercel → your project → **Settings** → **Environment Variables**
2. Edit the `BANNER_KEY` value
3. Go to **Deployments** and redeploy the latest deployment for the change to take effect
4. Update the README URL in any repository using the old key

### To reset the image cycle manually

1. Go to Supabase → **SQL Editor**
2. Run:

```sql
DELETE FROM shown_banners;
DELETE FROM rate_limit;
```

3. The next request will start a fresh cycle from all 30 images

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Banner shows 403 | Wrong key in URL | Check BANNER_KEY in Vercel env vars |
| Banner shows 500 | Supabase credentials wrong | Check SUPABASE_URL and SUPABASE_KEY |
| Banner shows 404 | Image file missing | Confirm `src/img/1.webp` through `30.webp` are in the repo |
| Banner not changing | GitHub cache | Wait a few minutes or open the URL directly in a browser |
| Deploy fails | `requirements.txt` error | Check Python package names and versions are spelled correctly |
| Rate limit row not updating | RLS still enabled | Run `ALTER TABLE rate_limit DISABLE ROW LEVEL SECURITY;` in SQL Editor |
