# YouTube Integration Setup

Connect your YouTube channel in ~5 minutes. Uploads always remain
approval-gated: the studio only ever calls the API after you press
**Approve Upload** and check the confirmation.

## 1. Create Google Cloud credentials

1. Go to <https://console.cloud.google.com/> and create (or select) a project.
2. **APIs & Services → Library** → enable **YouTube Data API v3**.
3. **APIs & Services → OAuth consent screen**
   - User type: *External* → fill app name ("AI Kids Video Studio") + emails.
   - Scopes: add `youtube.upload` and `youtube` (or pick them from
     YouTube Data API v3).
   - Test users: add your Google account while the app is unverified.
4. **Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URIs — add one per environment:
     - `http://localhost:8000/api/v1/youtube/callback` (dev)
     - `https://your-api-domain/api/v1/youtube/callback` (prod)

## 2. Configure the backend

```env
YOUTUBE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxxxxxxx
YOUTUBE_REDIRECT_URI=http://localhost:8000/api/v1/youtube/callback
```

Restart the backend. Settings → YouTube Connection now shows
"configured: true".

## 3. Connect your channel

Dashboard → **Settings → Connect YouTube Channel** → consent on Google
(the screen warns the app is unverified until you publish it — expected;
proceed with your own account). You are redirected back after consent and
the studio stores the refresh token **encrypted** (`provider_settings`).

**Multiple Google accounts?** The consent flow always opens Google's account
picker so you can choose the channel-owning Gmail, and Settings has an
optional email box that preselects it. Make sure that exact Gmail is listed
under **OAuth consent screen → Test users**, or Google will show
"Access blocked: this app has not completed verification". Connected the
wrong account? Hit **Disconnect** in Settings and connect again.

## 4. What uploads do

| Action | Behavior |
| --- | --- |
| Upload video | Resumable, 8 MB chunks, exponential-backoff retries on 5xx/transport |
| Metadata | Title (≤100 chars), description (+ synthetic-media disclosure), tags, category **Education (27)** |
| Audience | `madeForKids` + `selfDeclaredMadeForKids` per your checkbox (COPPA) |
| Privacy | `private` by default — a draft only you can see |
| Schedule | `publishAt` (RFC 3339) publishes automatically at that time |
| Thumbnail | Uploaded after the video succeeds (never fails the upload) |
| Status | `GET videos.list` refresh: upload/processing status tracked in history |
| Retry | Failed uploads resume via the retry endpoint with attempt counting |

## 5. Quota & verification notes

- Unverified apps have a 10,000 units/day quota — an `upload` costs 1,600
  units, so ~6 uploads/day. Request a quota increase for production scale.
- Publishing before Google verification review keeps a hidden "unverified
  app" warning during user consent — fine for personal channels; submit for
  verification review for public products.
- COPPA: this product marks uploads *made for kids* by default — comments,
  personalized ads and end screens are disabled by YouTube for such content.
- The description includes a synthetic-media disclosure ("fully animated
  educational content; no real people or events") in line with YouTube's
  altered-content requirements — keep it when editing descriptions.

## 6. Disconnecting

Settings → Disconnect removes stored tokens. Revoking access from
<https://myaccount.google.com/permissions> also works; the next upload
attempt then fails with a clear reconnect message.
