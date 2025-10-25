# How to Restart Backend After Adding Service Role Key

After adding `SUPABASE_SERVICE_ROLE_KEY` to your `.env` file:

## Option 1: If backend is running in a terminal
1. Go to the terminal where backend is running
2. Press `Ctrl+C` to stop it
3. Run: `./start_backend.sh`

## Option 2: Kill and restart
```bash
# Kill the backend process
pkill -f "uvicorn main:app"

# Start it again
cd /Users/raasin/Desktop/LEXAI
./start_backend.sh
```

## Option 3: Use the run script
```bash
cd /Users/raasin/Desktop/LEXAI/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Verify It's Working

After restart, you should see:
```
✓ Using Supabase service role key (bypasses RLS)
```

If you see this instead, the key is missing:
```
⚠ Using Supabase anon key (respects RLS) - you may need service role key for uploads
```

## Test Upload

Once restarted with the service role key:
1. Upload a PDF document
2. Check the **Library** tab
3. Your document should now appear!
4. Check Supabase dashboard → Table Editor → documents table

