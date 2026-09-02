# README Banner Actions Bundle

A collection of reusable GitHub Actions workflows for dynamically managing README banners. Automatically rotate banners, update release notes, and keep your README fresh with minimal configuration.

## Available Workflows

### 1. Update Banner
Automatically fetches and updates your README banner from the backend service.

**Triggers:**
- Schedule: Every 24 hours at 09:00 UTC
- Manual dispatch
- On push to main (ignores asset changes)
- Can be called as a reusable workflow

**Usage:**

```yaml
jobs:
  update:
    uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}
```

**Inputs:**
- `VERCEL_URL` (required): URL of your banner backend service

**Secrets:**
- `BANNER_KEY` (required): API key for authenticating with the banner service

**What it does:**
- Ensures your README has the banner reference
- Fetches the latest banner image from your backend
- Automatically commits and pushes changes
- Uses amended commits to prevent cluttering your history

---

### 2. Reset Banner Cycle
Resets the banner rotation cycle on the backend.

**Triggers:**
- Manual dispatch
- Can be called as a reusable workflow

**Usage:**

```yaml
jobs:
  reset:
    uses: 14ag/readme-banner/.github/workflows/readme-banner-reset.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}
```

**Inputs:**
- `VERCEL_URL` (required): URL of your banner backend service

**Secrets:**
- `BANNER_KEY` (required): API key for authenticating with the banner service

**What it does:**
- Sends a reset request to the backend `/reset` endpoint
- Restarts the banner rotation cycle

---

### 3. Release Notes Banner
Automatically adds the current banner to your release notes.

**Triggers:**
- On release published
- Can be called as a reusable workflow

**Usage:**

```yaml
jobs:
  release-notes:
    uses: 14ag/readme-banner/.github/workflows/release-notes-banner.yml@main
```

**What it does:**
- Triggers when a release is published
- Prepends the banner image to the release body
- Only modifies the latest release
- Prevents duplicate banners

---

## Setup Instructions

### 1. Basic Setup (Using Update Workflow Only)

Add these to your repository:

**Repository Variables (Settings → Secrets and variables → Variables):**
```
VERCEL_URL: https://your-banner-service.vercel.app
```

**Repository Secrets (Settings → Secrets and variables → Secrets):**
```
BANNER_KEY: your-api-key-here
```

### 2. Add to Your Workflow

Reference the update workflow in your `.github/workflows/your-workflow.yml`:

```yaml
name: Your Workflow

on:
  push:
    branches:
      - main

jobs:
  your-job:
    runs-on: ubuntu-latest
    steps:
      # Your steps here
      - run: echo "Your job runs first"

  update-banner:
    needs: your-job
    uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}
```

### 3. Create Assets Folder

The workflows expect an `assets/` folder:

```bash
mkdir -p assets
```

The banner will be saved as `assets/banner.webp`.

---

## Backend Requirements

Your backend service must implement these endpoints:

### GET `/banner`
Fetches the current banner image.

**Headers:**
- `X-Banner-Key`: API key for authentication
- `repo-name`: Name of the requesting repository

**Response:**
- WebP image binary data

### POST `/reset`
Resets the banner rotation cycle.

**Headers:**
- `X-Banner-Key`: API key for authentication
- `repo-name`: Name of the requesting repository

**Response:**
- Success/error message

---

## Example Workflows

### Option A: Use Only Update Banner (Recommended)
```yaml
# .github/workflows/banner-update.yml
name: Update Banner
on:
  push:
    branches:
      - main

jobs:
  update-banner:
    uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}
```

### Option B: Use All Three Workflows
```yaml
# .github/workflows/banner-full.yml
name: Banner Management
on:
  push:
    branches:
      - main
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        default: 'update'
        type: choice
        options:
          - update
          - reset
          - release-notes

jobs:
  update:
    if: ${{ github.event_name == 'push' || github.event.inputs.action == 'update' }}
    uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}

  reset:
    if: ${{ github.event.inputs.action == 'reset' }}
    uses: 14ag/readme-banner/.github/workflows/readme-banner-reset.yml@main
    with:
      VERCEL_URL: ${{ vars.VERCEL_URL }}
    secrets:
      BANNER_KEY: ${{ secrets.BANNER_KEY }}

  release-notes:
    if: ${{ github.event_name == 'release' || github.event.inputs.action == 'release-notes' }}
    uses: 14ag/readme-banner/.github/workflows/release-notes-banner.yml@main
```

---

## Troubleshooting

### Banner not updating
- Check that `VERCEL_URL` and `BANNER_KEY` are set correctly in repository variables/secrets
- Verify your backend service is running and accessible
- Check the workflow run logs in the Actions tab

### Workflow fails with 401/403
- Verify `BANNER_KEY` is correct
- Ensure the API key has appropriate permissions on your backend

### README doesn't have banner reference
- The workflow automatically adds `![Banner](./assets/banner.webp)` to the top of README.md
- Make sure the repository has write permissions (`contents: write`)

### Multiple banner lines in README
- Edit README.md and remove duplicate lines manually
- The workflow won't add duplicates on subsequent runs

---

## Version Pinning

For stability, pin to a specific release:

```yaml
uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@v1.0.0
```

Or use `@main` for the latest development version:

```yaml
uses: 14ag/readme-banner/.github/workflows/readme-banner-update.yml@main
```

---

## Contributing

Found an issue or have a suggestion? Open an issue or PR in the repository!

---

## License

Check the LICENSE file in the repository.
