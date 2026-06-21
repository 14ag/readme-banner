![Banner](./assets/banner.webp)

# Your Project Name

this system is a backend that rotatates the banner image on GitHub README files. it is trigered by the github action `update-banner`

## Endpoints

- `GET /health` returns service status.
- `GET /banner` returns one WebP banner image.
- `POST /reset` resets the cycle when called with `X-Banner-Key`.

read [Deployment Notes](DEPLOY.md) for setup instructions


GitHub proxies README images through its camo CDN, so banner changes may appear after a few minutes
