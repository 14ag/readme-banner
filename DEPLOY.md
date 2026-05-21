# Deployment Guide: Random README Banner

You need three accounts: **GitHub**, **Supabase**, and **Vercel**.
No local installs are required to deploy. You only need a browser.

---

## Part 1 — Supabase: Create the Database

### Step 1.1 — Create a new project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click **New project**
3. Give it a name, e.g. `readme-banner`
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
3. Name it `readme-banner`
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
git remote add origin https://github.com/YOUR_USERNAME/readme-banner.git
git push -u origin main
```

If you do not have Git locally, use GitHub's web upload:

1. Open the repository on GitHub
2. Click **Add file** → **Upload files**
3. Drag and drop all your project files and folders
4. Click **Commit changes**

> Make sure `src/img/` with all 30 WebP files is included.
> Make sure `.env` is **not** uploaded. It should be in your `.gitignore`.

### Step 2.3 — Configure GitHub Actions credentials

The README does not contain the banner key. GitHub Actions stores the key as a
secret, fetches the banner from Vercel, saves it as `assets/banner.webp`, and
commits that file back to the repository.

1. In your repository go to **Settings** → **Secrets and variables** → **Actions**
2. Under the **Secrets** tab, click **New repository secret**
3. Name: `BANNER_KEY`
4. Value: the unique key you invented
5. Click **Add secret**

Then add the public Vercel URL as a repository variable:

1. In the same **Actions** page, open the **Variables** tab
2. Click **New repository variable**
3. Name: `VERCEL_URL`
4. Value: your Vercel project URL with no trailing slash, e.g.
   `https://readme-banner.vercel.app`
5. Click **Add variable**

---

## Part 3 — Vercel: Deploy the Backend

### Step 3.1 — Import the project

1. Go to [https://vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Under **Import Git Repository** find your `readme-banner` repo
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
`https://readme-banner-abc123.vercel.app`

---

## Part 4 — Generate the README Banner Asset

### Step 4.1 — Confirm the README image path

The README should use the committed banner asset, not the backend URL:

```markdown
![Banner](./assets/banner.webp)
```

This keeps `BANNER_KEY` out of the public README.

### Step 4.2 — Run the banner workflow once

After `BANNER_KEY` and `VERCEL_URL` are configured:

1. Go to **Actions** → **Update Banner**
2. Click **Run workflow**
3. Wait for the run to finish
4. Confirm the workflow commits `assets/banner.webp`

The workflow also runs every 6 hours and on pushes to `main`.

### Step 4.3 — How rotation works

The workflow calls:

```text
GET ${VERCEL_URL}/banner?key=${BANNER_KEY}
```

It saves the response to `assets/banner.webp`, commits the file only when it
changes, and pushes the commit to `main`. The README then displays the committed
file directly.

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

### Step 5.2 — Test the private banner endpoint

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

### Step 5.4 — Verify the GitHub Actions banner

1. Go to **Actions** → **Update Banner**
2. Run the workflow manually
3. Confirm the run succeeds
4. Confirm `assets/banner.webp` exists in the repository
5. Confirm the rendered README shows the banner without a key in the image URL

### Step 5.5 — Check Supabase after the first request

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
3. Go to GitHub → repository → **Settings** → **Secrets and variables** → **Actions**
4. Update the `BANNER_KEY` secret to the same value
5. Go to **Deployments** in Vercel and redeploy the latest deployment for the change to take effect
6. Run the **Update Banner** workflow manually

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
| Update Banner action builds `/banner?key=...` | VERCEL_URL was added as a secret instead of a variable | Add VERCEL_URL under Actions Variables |
| Update Banner action shows 403 | GitHub BANNER_KEY secret does not match Vercel BANNER_KEY | Update the GitHub secret or Vercel env var so they match |
| Banner shows 500 | Supabase credentials wrong | Check SUPABASE_URL and SUPABASE_KEY |
| Banner shows 404 | Image file missing | Confirm `src/img/1.webp` through `30.webp` are in the repo |
| README banner missing | assets/banner.webp has not been created yet | Run the Update Banner workflow manually |
| Banner not changing | 35-second backend cache window or same fetched image file | Wait 35 seconds, then rerun the Update Banner workflow |
| Deploy fails | `requirements.txt` error | Check Python package names and versions are spelled correctly |
| Rate limit row not updating | RLS still enabled | Run `ALTER TABLE rate_limit DISABLE ROW LEVEL SECURITY;` in SQL Editor |
