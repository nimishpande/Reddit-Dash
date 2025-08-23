import praw
import json
import sys
import time
import os
from datetime import datetime, timezone, timedelta

# Helper to get canonical INCI name from separated_ingredients
def get_canonical_inci_name(ingredient):
    sep_dir = "IngredientsScrapper/separated_ingredients"
    # Try to find a file with this ingredient name (minimal sanitization)
    safe_name = ingredient.replace('/', '_').replace('\\', '_')
    path = os.path.join(sep_dir, f"{safe_name}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Try to get canonical name from search_results[0]['inci_name']
            if data.get('search_results') and data['search_results'][0].get('inci_name'):
                return data['search_results'][0]['inci_name']
        except Exception:
            pass
    return ingredient

def read_ingredient_keywords(filename='ingredient.txt'):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    # Step 1: Authenticate
    try:
        reddit = praw.Reddit(
            client_id="T_5eO0s-SeLJnEnsxrbx2Q",
            client_secret="9y3zJDkBTbnYERNI8a4cfUNvfTc8Ww",
            user_agent="ingredient scraper by /u/Traditional_Cup7724"
        )
        reddit.user.me()
        print("[OK] Authentication successful!")
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        sys.exit(1)

    ingredients = read_ingredient_keywords('ingredient.txt')
    print(f"[INFO] Processing {len(ingredients)} ingredients from ingredient.txt...")
    for idx, ingredient in enumerate(ingredients, 1):
        print(f"\n[{idx}/{len(ingredients)}] Processing: {ingredient}")
        canonical_inci = get_canonical_inci_name(ingredient)
        # Set up search terms for this ingredient
        OR_IDENTIFIERS = [ingredient]
        AND_IDENTIFIERS = []
        search_terms = []
        or_query = " OR ".join([
            f'title:"{term}"' for term in OR_IDENTIFIERS
        ] + [
            f'selftext:"{term}"' for term in OR_IDENTIFIERS
        ])
        search_terms.append(f'({or_query})')
        SEARCH_QUERY = " AND ".join(search_terms)
        identifier_str = canonical_inci.replace(' ', '_').replace('/', '_').replace('-', '_')
        # Reddit search config
        MAX_COMMENTS = 30
        MAX_POSTS = 139
        UNLIMITED_MODE = True
        INCLUDE_NESTED_COMMENTS = False
        results = []
        # Fetch posts
        try:
            posts = list(reddit.subreddit("all").search(
                SEARCH_QUERY,
                sort="top",
                time_filter="all" if UNLIMITED_MODE else "year",
                limit=MAX_POSTS
            ))
            print(f"[INFO] Found {len(posts)} posts for {ingredient}")
            for post in posts:
                # Extract comments
                try:
                    post.comments.replace_more(limit=0)
                    all_comments = []
                    for comment in post.comments:
                        if hasattr(comment, 'author') and comment.author:
                            all_comments.append({
                                "author": comment.author.name,
                                "body": comment.body.strip(),
                                "score": comment.score,
                                "is_top_level": True
                            })
                    all_comments.sort(key=lambda x: x["score"], reverse=True)
                    all_comments = all_comments[:MAX_COMMENTS]
                except Exception as e:
                    print(f"[WARN] Error extracting comments: {e}")
                    all_comments = []
                results.append({
                    "subreddit": post.subreddit.display_name,
                    "post_id": post.id,
                    "title": post.title,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created": datetime.fromtimestamp(post.created_utc, timezone.utc).isoformat(),
                    "body": post.selftext,
                    "flair_text": getattr(post, "link_flair_text", None),
                    "flair_template_id": getattr(post, "link_flair_template_id", None),
                    "comments": all_comments,
                    "comment_breakdown": {
                        "total_collected": len(all_comments),
                        "top_level": len(all_comments),
                        "nested_replies": 0
                    }
                })
            # Compose output
            output = {
                "ingredient": canonical_inci,
                "results": results
            }
            # Write output
            out_dir = "IngredientsScrapper/raw data"
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{canonical_inci}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"[OK] Wrote {out_path} ({len(results)} posts)")
        except Exception as e:
            print(f"[FATAL] Error processing {ingredient}: {e}")
            print("Aborting batch.")
            return
    print("\n[INFO] All ingredients processed.")

if __name__ == "__main__":
    main()
