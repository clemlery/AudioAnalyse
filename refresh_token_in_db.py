#!/usr/bin/env python3
"""
refresh_token_in_db.py — Get fresh Spotify token via browser and save to DB
"""

import psycopg2
from pipeline.factory import BrowserTokenSource
from core.config import logger

if __name__ == "__main__":
    print("[*] Generating fresh Spotify token via browser...")
    try:
        token_source = BrowserTokenSource()
        ctx = token_source.get_context()

        print("[+] Got fresh access token!")

        # Save to DB
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="lyra",
            user="postgres",
            password="1234"
        )
        cur = conn.cursor()

        # Get the first user (or create one if needed)
        cur.execute("SELECT id FROM \"user\" LIMIT 1")
        user_id_row = cur.fetchone()

        if user_id_row:
            user_id = user_id_row[0]
            cur.execute(
                'UPDATE "user" SET access_token = %s, token_last_update = NOW() WHERE id = %s',
                (ctx.access_token, user_id)
            )
            print(f"[+] Updated token in database for user {user_id}")
        else:
            print("[-] No users in database. Create one via web interface first.")
            cur.close()
            conn.close()
            exit(1)

        conn.commit()
        cur.close()
        conn.close()

        print("\n" + "="*60)
        print("FRESH ACCESS TOKEN (saved to DB)")
        print("="*60)
        print(ctx.access_token)
        print("="*60)
        print("\nYou can now use this token for imports:")
        print(f'  python test_dataset_import.py "{ctx.access_token}" ./data/dataset/dataset.csv 100')

    except Exception as e:
        print(f"[ERROR] {e}")
        logger.error(f"Failed: {e}", exc_info=True)
        exit(1)

