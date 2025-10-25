# Supabase Authentication Setup Guide

## Prerequisites

1. A Supabase account (sign up at [supabase.com](https://supabase.com))
2. A Supabase project created

## Setup Steps

### 1. Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings** > **API**
3. Copy the following values:
   - **Project URL** (under Project URL)
   - **anon/public key** (under Project API keys)

### 2. Configure Environment Variables

Create a `.env.local` file in the root of the `LexAIScholar` directory with the following content:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Replace `your_supabase_project_url` and `your_supabase_anon_key` with your actual Supabase credentials.

### 3. Install Dependencies

Run the following command to install all required dependencies:

```bash
cd LexAIScholar
npm install
```

### 4. Configure Supabase Authentication

In your Supabase dashboard:

1. Go to **Authentication** > **Providers**
2. Enable **Email** provider
3. Configure email templates (optional)
4. Set up redirect URLs if needed:
   - Go to **Authentication** > **URL Configuration**
   - Add `http://localhost:3000` for local development

### 5. Database Setup (Optional)

If you want to store additional user data, you can create tables in Supabase:

1. Go to **SQL Editor** in your Supabase dashboard
2. Run the following SQL to create a profiles table:

```sql
-- Create profiles table
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  full_name text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security
alter table profiles enable row level security;

-- Create policies
create policy "Users can view their own profile"
  on profiles for select
  using (auth.uid() = id);

create policy "Users can update their own profile"
  on profiles for update
  using (auth.uid() = id);

-- Create trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

### 6. Run the Application

Start the development server:

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to see your application with authentication enabled.

## Features Implemented

✅ **Authentication Components:**
- Login form with email/password
- Signup form with validation
- Modal-based authentication UI
- Auth state management with React Context

✅ **User Features:**
- User registration
- User login
- User logout
- Session persistence
- Auto-refresh tokens

✅ **UI Integration:**
- Login/Signup buttons in navigation
- User email display when authenticated
- Conditional rendering based on auth state
- Beautiful modal design with Tailwind CSS

## Testing Authentication

1. **Sign Up:**
   - Click "Sign Up" in the navigation
   - Fill in the signup form
   - Check your email for confirmation (if email confirmation is enabled)

2. **Sign In:**
   - Click "Login" in the navigation
   - Enter your credentials
   - You should be redirected and see your email in the navigation

3. **Sign Out:**
   - Click "Sign Out" button in the navigation
   - You should be logged out and see Login/Signup buttons again

## Troubleshooting

### Issue: "Supabase URL or Anon Key is not set"

**Solution:** Make sure your `.env.local` file is created and contains the correct values.

### Issue: Authentication not working

**Solutions:**
1. Verify your Supabase credentials are correct
2. Check that email authentication is enabled in Supabase
3. Ensure your redirect URLs are configured correctly
4. Check browser console for error messages

### Issue: npm install fails

**Solution:** Make sure you're in the `LexAIScholar` directory and have Node.js installed (version 18+ recommended).

## Next Steps

- Implement password reset functionality
- Add social authentication providers (Google, GitHub, etc.)
- Create protected routes that require authentication
- Add user profile management
- Implement email verification flow

