# scripts/combined_stats.py
import json, os, requests

GH_TOKEN = os.getenv("GH_TOKEN")
USER = "88n77"
ORG = "88n77NODES"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json"
}

GQL = "https://api.github.com/graphql"

def sum_stars_for_owner(owner, is_org=False):
    # Пагінація по 100 реп
    stars = 0
    repos = 0
    cursor = None
    query = """
    query($owner:String!, $cursor:String, $isOrg:Boolean!) {
      user(login:$owner) @skip(if:$isOrg) {
        repositories(first:100, after:$cursor, privacy:PUBLIC, isFork:false, ownerAffiliations:OWNER) {
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
      }
      organization(login:$owner) @include(if:$isOrg) {
        repositories(first:100, after:$cursor, privacy:PUBLIC, isFork:false) {
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
      }
    }
    """
    while True:
        variables = {"owner": owner, "cursor": cursor, "isOrg": is_org}
        r = requests.post(GQL, headers=HEADERS, json={"query": query, "variables": variables})
        r.raise_for_status()
        data = r.json()["data"]
        key = "organization" if is_org else "user"
        repos_edge = data[key]["repositories"]
        for n in repos_edge["nodes"]:
            stars += n["stargazerCount"]
            repos += 1
        if repos_edge["pageInfo"]["hasNextPage"]:
            cursor = repos_edge["pageInfo"]["endCursor"]
        else:
            break
    return stars, repos

user_stars, user_repos = sum_stars_for_owner(USER, is_org=False)
org_stars,  org_repos  = sum_stars_for_owner(ORG,  is_org=True)

combined_stars = user_stars + org_stars
combined_repos = user_repos + org_repos

# Shields endpoint JSON
os.makedirs("docs", exist_ok=True)
with open("docs/combined-stars.json", "w", encoding="utf-8") as f:
    json.dump({
        "schemaVersion": 1,
        "label": "Combined Stars",
        "message": str(combined_stars),
        "color": "orange"
    }, f)

with open("docs/combined-repos.json", "w", encoding="utf-8") as f:
    json.dump({
        "schemaVersion": 1,
        "label": "Combined Repos",
        "message": str(combined_repos),
        "color": "blue"
    }, f)

print(f"User: {USER} -> stars={user_stars} repos={user_repos}")
print(f"Org:  {ORG}  -> stars={org_stars}  repos={org_repos}")
print(f"Combined -> stars={combined_stars} repos={combined_repos}")
