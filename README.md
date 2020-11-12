# WinCom2020
<p align="center">
  <a href="https://github.com/Mike7518/WinCom2020.git">
    <img src="images/results.png" alt="Wincom 2020 results">
  </a>
</p>

## Getting Started
### Required modules
This project relies on Python 3 and Flask for the REST API, and pymongo for database access (both server and DB tool).

### Installation

1. Create a MongoDB Atlas cloud database at [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)

2. Clone this repo
```sh
git clone https://github.com/Mike7518/WinCom2020.git
cd WinCom2020
```

3. Install Python and dependencies
```sh
sudo apt install python3
sudo python3 -m pip install -r requirements.txt
```

4. Enter your credentials in `credentials.py` as follows.
```python3
username = "USERNAME"
password = "PASSWORD"
cluster_url = "MONGO_ATLAS_URL"
```

<br>
Mikail BASER & Jordy AQUITEME
