# `binderhub-frontend`

The default frontend for [BinderHub](https://binderhub.readthedocs.io/).

## Usage

```html
<html>
<head>
  <link href="dist/styles.css" rel="stylesheet"></link>
  <script>
    window.pageConfig = {
      "badgeBaseUrl": "https://mybinder.org/",
      "baseUrl": "/",
      "repoProviders": [
          {
          "detect": {
              "regex": "^(https?://github.com/)?(?\u003crepo\u003e.*[^/])/?"
          },
          "displayName": "GitHub",
          "id": "gh",
          "ref": { "default": "HEAD", "enabled": true },
          "repo": {
              "label": "GitHub repository name or URL",
              "placeholder": "example: yuvipanda/requirements or https://github.com/yuvipanda/requirements",
              "urlEncode": false
          },
          "spec": { "validateRegex": "[^/]+/[^/]+/.+" }
          }
      ]
    };
  </script>
</head>
<body>
  <div id="root"></div>
</body>
<script src="dist/bundle.js"></script>
</html>
```
