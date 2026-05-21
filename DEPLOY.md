# Deployment Guide: Random README Banner

You need three accounts: **GitHub**, **Supabase**, and **Vercel**.
No local installs are required to deploy. You only need a browser.

---

## Part 1 Supabase: Create the Database

### Step 1.1 Create a new project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click **New project**
3. Give it a name, e.g. `readme-banner`
4. Choose a region close to you
5. Set a database password (save it somewhere safe)
6. Click **Create new project**

### Step 1.2 Create the tables

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

ALTER TABLE shown_banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit     ENABLE ROW LEVEL SECURITY;
```

5. Go to **Table Editor** in the sidebar and confirm both tables appear

### Step 1.3 Copy your credentials

1. In the sidebar go to **Integrations** → **Data API**
2. Copy and save your **API URL**
   - It should look like `https://abcdefgh.supabase.co/rest/v1/`
3. In the sidebar go to **Project Settings** → **API Keys**
4. Copy and save **secret key**:
   - It starts with `sb_secret_`

You will need both in Part 3.

---

## Part 2 GitHub: Repository setup

### Step 2.1 Clone the repository

**Clone locally**

```bash
git clone https://github.com/14ag/readme-banner.git
cd readme-banner
```

### Step 2.2 Make a deployable commit

Before you import the project into Vercel, make sure the latest commit message
contains `vercel`. The `vercel.json` file intentionally skips builds for other
commits so banner update commits do not redeploy the backend.

Make any small setup change, then commit and push:
Note that you should configure your remote repo and branch names 

```bash
git add .
git commit -m "setup vercel deploy"
git push
```
If you do not have Git locally:

1. Open your fork on GitHub
2. Navigate to the file you want to edit
3. Click the **pencil icon** to edit, or **Add file** → **Upload files** for new files
4. In the **Commit changes** box, make sure your message includes the word **vercel**
5. Click **Commit changes**


### Step 2.3 Configure GitHub Actions credentials

The README does not contain the banner key. GitHub Actions stores the key as a
secret, fetches the banner from Vercel, saves it as `assets/banner.webp`, then
commits that file back to the repository.

1. In your repository go to **Settings** → **Secrets and variables** → **Actions**
2. Under the **Secrets** tab, click **New repository secret**
3. Name: `BANNER_KEY`
4. Value: the unique key you invented
   - Use a long random value
   - Letters, numbers, `_`, and `-` are easiest for browser testing
5. Click **Add secret**

---

## Part 3 Vercel: Deploy the Backend

### Step 3.1 Import the project

1. Go to [https://vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Under **Import Git Repository** find your `readme-banner` repo
4. Click **Import**

### Step 3.2 Configure the project

On the configuration screen:

- **Framework Preset**: select **Other** (not Next.js)
- **Root Directory**: leave it as `/` (the project root)
- **Build Command**: leave it empty
- **Output Directory**: leave it empty

Vercel detects FastAPI automatically from `requirements.txt`.

### Step 3.3 Add environment variables

Still on the configuration screen, scroll to **Environment Variables**.

Add these three variables one by one:

| Name          | Value                                      |
|---------------|--------------------------------------------|
| SUPABASE_DATA_API_URL | your Data API URL from Step 1.3    |
| SUPABASE_SECRET_KEY | your secret key from Step 1.3         |
| BANNER_KEY    | the same unique key you set in Step 2.3    |

Click **Add** after each one.

### Step 3.4 Deploy

Click **Deploy**.

Vercel will:
- Clone your repository
- Install the packages from `requirements.txt`, including `supabase==2.30.0`
- Deploy the FastAPI app as a serverless function


When finished you will see **Congratulations!** and a live URL like:
`https://readme-banner-abc123.vercel.app/`

### Step 3.5 Add the Vercel URL to GitHub Actions

1. Go back to GitHub → your repository → **Settings** → **Secrets and variables** → **Actions**
2. Open the **Variables** tab
3. Click **New repository variable**
4. Name: `VERCEL_URL`
5. Value: your Vercel project URL, e.g. `https://readme-banner-abc123.vercel.app/`
   - Paste the URL as Vercel shows it
6. Click **Add variable**

---

## Part 4 Generate the README Banner Asset

### Step 4.1 Confirm the README image path

The README should use the committed banner asset, not the backend URL:

```markdown
![Banner](./assets/banner.webp)
```

This keeps `BANNER_KEY` out of the public README.

### Step 4.2 Run the banner workflow once

After `BANNER_KEY` and `VERCEL_URL` are configured:

1. Go to **Actions** → **Update Banner**
2. Click **Run workflow**
3. Wait for the run to finish
4. Confirm the workflow commits `assets/banner.webp`

The workflow also runs every 12 hours and on pushes to `main`.

### Step 4.3 How rotation works

The workflow trims trailing slashes from `VERCEL_URL`, then calls:

```text
GET https://YOUR_VERCEL_DOMAIN.vercel.app/banner
X-Banner-Key: BANNER_KEY
```

It saves the response to `assets/banner.webp`, commits the file only when it
changes, and pushes the commit to `main`. The README then displays the committed
file directly.

---

## Part 5 Verify Everything Works

### Step 5.1 Test the health endpoint

Open this URL in your browser:

```
https://YOUR_VERCEL_DOMAIN.vercel.app/health
```

You should see:

```json
{"status": "ok"}
```

### Step 5.2 Test the private banner endpoint

Open this URL in your browser (replace the values):

```
https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=YOUR_BANNER_KEY_VALUE
```

You should see a WebP image displayed in your browser.


### Step 5.3 Verify the GitHub Actions banner

1. Go to **Actions** → **Update Banner**
2. Run the workflow manually
3. Confirm the run succeeds
4. Confirm `assets/banner.webp` exists in the repository
5. Confirm the rendered README shows the banner without a key in the image URL

### Step 5.4 Check Supabase after the first request

1. Go to Supabase → **Table Editor** → `shown_banners`
2. You should see one row with an `image_number` between 1 and 30
3. Go to `rate_limit` → you should see one row with `id = 1`

If all of the above pass, the system is working correctly.

---

## Part 6 Future Updates

### To update the backend code

1. Edit the file locally and push to GitHub
2. Use a commit message that contains `vercel`
3. Vercel redeploys that commit on `main`

### To change the BANNER_KEY

1. Go to Vercel → your project → **Settings** → **Environment Variables**
2. Edit the `BANNER_KEY` value
3. Go to GitHub → repository → **Settings** → **Secrets and variables** → **Actions**
4. Update the `BANNER_KEY` secret to the same value
5. Go to **Deployments** in Vercel and redeploy the latest deployment for the change to take effect
6. Run the **Update Banner** workflow manually

### To reset the image cycle manually

Use the reset workflow for normal resets:

1. Go to **Actions** → **Reset Banner Cycle**
2. Click **Run workflow**
3. Wait for the run to finish
4. Run **Update Banner** once if you want the README image refreshed immediately

The reset workflow calls:

```text
POST https://YOUR_VERCEL_DOMAIN.vercel.app/reset
X-Banner-Key: BANNER_KEY
```

The reset endpoint accepts `BANNER_KEY` through the `X-Banner-Key` header.


The next banner request starts a fresh cycle from all 30 images.


### To add the banner to another repository
1. Add the same README image tag to the new repository, `![Banner](./assets/banner.webp)`
2. Add the same `BANNER_KEY` as a secret to the new repository's GitHub Actions secrets
3. Add the same `VERCEL_URL` as a variable to the new repository's GitHub Actions variables
4. Add the same runners to the new repository's GitHub Actions workflows, in `.github/workflows/update_banner.yml` and `.github/workflows/reset_banner_cycle.yml`:

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Banner shows 403 | Wrong key in URL | Check BANNER_KEY in Vercel env vars |
| Update Banner action calls `/banner` with no domain | VERCEL_URL was added as a secret instead of a variable, or was not added | Add VERCEL_URL under Actions Variables |
| Update Banner action shows 403 | GitHub BANNER_KEY secret does not match Vercel BANNER_KEY | Update the GitHub secret or Vercel env var so they match |
| Banner shows 500 | Supabase credentials wrong | Check SUPABASE_DATA_API_URL and SUPABASE_SECRET_KEY |
| Banner shows 404 | Image file missing | Confirm `src/img/1.webp` through `30.webp` are in the repo |
| README banner missing | assets/banner.webp has not been created yet | Run the Update Banner workflow manually |
| Banner not changing | 35-second backend cache window or same fetched image file | Wait 35 seconds, then rerun the Update Banner workflow |
| Reset Banner Cycle action shows 403 | GitHub BANNER_KEY secret does not match Vercel BANNER_KEY | Update the GitHub secret or Vercel env var so they match |
| Reset Banner Cycle action calls `/reset` with no domain | VERCEL_URL was added as a secret instead of a variable, or was not added | Add VERCEL_URL under Actions Variables |
| Deploy fails | `requirements.txt` error | Check Python package names and versions are spelled correctly |
| Rate limit row not updating | Supabase key is publishable/anon or wrong | Use a backend-only secret key or service_role key in Vercel |
| Update Banner action cannot push | Branch protection blocks GitHub Actions commits | Allow GitHub Actions to push to `main`, or switch the workflow to open a pull request |
