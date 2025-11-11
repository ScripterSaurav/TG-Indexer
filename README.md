# Telegram Indexer

> A powerful Python web application that indexes Telegram channels and chats, allowing you to browse, search, and download media files through a web interface.


![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Telethon](https://img.shields.io/badge/Telethon-Library-green?logo=telegram)
![License](https://img.shields.io/badge/License-GPL-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 📋 To-Do List

- [ ] Implement multi-client worker bots support
- [ ] Add cache system support
- [ ] Implement channel lock functionality

## ✨ Features

- 🔍 **Smart Indexing** - Index one or multiple Telegram channels/chats
- 📱 **Web Interface** - Browse messages and media files directly in your browser
- 🔎 **Advanced Search** - Search through all indexed content
- 📥 **Media Download** - Download files via browser or download managers
- 🔒 **Authentication** - Optional username/password protection
- 🎯 **Selective Indexing** - Choose specific chats or index all available

## 🚀 Quick Deploy

### Step-by-Step Deployment

1️⃣. **Clone the repository**
```bash
git clone https://github.com/odysseusmax/tg-index.git
cd tg-index
```

2️⃣. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3️⃣. **Install dependencies**
```bash
pip install -U -r requirements.txt
```

## ⚙️ Configuration

4️⃣. **Environment Variables**

| Variable Name                        | Value                                                                                                                                                          |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API_ID` (required)                  | Telegram api_id obtained from <https://my.telegram.org/apps>.                                                                                                  |
| `API_HASH` (required)                | Telegram api_hash obtained from <https://my.telegram.org/apps>.                                                                                                |
| `INDEX_SETTINGS` (required)          | See the below description.                                                                                                                                     |
| `SESSION_STRING` (required)          | String obtained by running `$ python3 app/generate_session_string.py`. (Login with the telegram account which is a participant of the given channel (or chat). |
| `PORT` (optional)                    | Port on which app should listen to, defaults to 8080.                                                                                                          |
| `HOST` (optional)                    | Host name on which app should listen to, defaults to 0.0.0.0.                                                                                                  |
| `DEBUG` (optional)                   | Give `true` to set logging level to debug, info by default.                                                                                                    |
| `BLOCK_DOWNLOADS` (optional)         | Enable downloads or not. If any value is provided, downloads will be disabled.                                                                                 |
| `RESULTS_PER_PAGE` (optional)        | Number of results to be returned per page defaults to 20.                                                                                                      |
| `TGINDEX_USERNAME` (optional)        | Username for authentication, defaults to `''`.                                                                                                                 |
| `PASSWORD` (optional)                | Password for authentication, defaults to `''`.                                                                                                                 |
| `SHORT_URL_LEN` (optional)           | Url length for aliases                                                                                                                                         |
| `SESSION_COOKIE_LIFETIME` (optional) | Number of minutes, for which authenticated session is valid for, after which user has to login again. defaults to 60.                                          |
| `SECRET_KEY` (optional)              | 32 characters long string for signing the session cookies, required if authentication is enabled.                                                              |

### Generating Session String

> Run the included script to generate your session string or use this tool

[Telethon Session Generator tool](https://telegram.tools/session-string-generator#telethon,user)


## Configuration Options:

- `index_all` - Index all available chats (`true`/`false`)
- `index_private` - Include private chats (requires `index_all: true`)
- `index_group` - Include groups (requires `index_all: true`)
- `index_channel` - Include channels (requires `index_all: true`)
- `exclude_chats` - Array of chat IDs to exclude
- `include_chats` - Array of specific chat IDs to index (requires `index_all: false`)


## 🔧 Utility Scripts

### Generate Secret Key

```python
import secrets
import string

def generate_secret_key():
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(characters) for _ in range(32))
    return secret_key

print(generate_secret_key())
```

## 🎯 Usage

5️⃣. Start the application:

```bash
python3 -m app
```

The web interface will be available at `http://localhost:8080` (or your configured host/port).


## 🔒 Security Notes

- Use the provided `generate_session_string.py` script for safe session generation
- Always set a strong `SECRET_KEY` when enabling authentication
- Consider using `BLOCK_DOWNLOADS` in public deployments
- Regularly update dependencies for security patches

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 🧑‍💻 Author & Credits

**Credit:** [odysseusmax/tg-index](https://github.com/odysseusmax/tg-index) 

**Fixed & Modified:** ✨ by [Me](#)


## 📄 License

This project is licensed under the **The GNU General Public License** - see the [LICENSE](LICENSE) file for details.

---

**Note**: Make sure you have appropriate permissions to access and index the Telegram channels/chats you're targeting. Always comply with Telegram's Terms of Service and respect privacy guidelines.
