# QA Catch: Volatile Environment Variables in Production
When using os.environ.get('KEY', generate_key()), ensure that the fallback generation is saved persistently or the user is warned. Otherwise, ephemeral server restarts (like on Render) will wipe the key and permanently lock all encrypted database records.
