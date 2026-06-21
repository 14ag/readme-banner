![Banner](./assets/banner.webp)

# Your Project Name

this system is a backend that rotatates the banner image on GitHub README files. it is trigered by the github action `update-banner`

## Endpoints

- `GET /health` check service status
- `GET /banner` gets one cool banner image
- `POST /reset` resets the cycle 

read [Deployment Notes](DEPLOY.md) for setup instructions


GitHub proxies README images through its camo CDN, so banner changes may appear after a few minutes
