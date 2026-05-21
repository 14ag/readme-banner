![Banner](./assets/banner.webp)

# Your Project Name

Random rotating README banner backend for GitHub README files.

## Endpoints

- `GET /health` returns service status.
- `GET /banner?key=YOUR_KEY` returns one WebP banner image.
- `POST /reset` resets the cycle when called with `X-Banner-Key`.

## [Deployment Notes](DEPLOY.md)

Set these environment variables in Vercel:

- `SUPABASE_DATA_API_URL` like `https://your-project-ref.supabase.co/rest/v1/`
- `SUPABASE_SECRET_KEY`
- `BANNER_KEY`

Set `VERCEL_URL` as a GitHub Actions repository variable. A trailing slash is OK.

GitHub proxies README images through its camo CDN, so banner changes may appear after a few minutes.
