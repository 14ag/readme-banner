![Banner](./assets/banner.webp)

# Your Project Name

Random rotating README banner backend for GitHub README files.

## Endpoints

- `GET /health` returns service status.
- `GET /banner?key=YOUR_KEY` returns one WebP banner image.

## Deployment Notes

Set these environment variables in Vercel:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BANNER_KEY`

GitHub proxies README images through its camo CDN, so banner changes may appear after a few minutes.
