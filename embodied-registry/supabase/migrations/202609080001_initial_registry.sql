create extension if not exists pgcrypto;

create type public.verification_status as enum ('self_tested', 'runner_verified', 'reproduced', 'lab_verified', 'certified');
create type public.evaluation_visibility as enum ('public', 'private');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  handle text unique check (handle ~ '^[a-z0-9][a-z0-9-]{2,38}$'),
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now()
);

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{2,62}$'),
  name text not null,
  created_by uuid not null references public.profiles(id),
  created_at timestamptz not null default now()
);

create table public.organization_members (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'member')),
  created_at timestamptz not null default now(),
  primary key (organization_id, profile_id)
);

create table public.skills (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{2,90}$'),
  name text not null,
  summary text not null,
  owner_profile_id uuid references public.profiles(id),
  owner_organization_id uuid references public.organizations(id),
  source_url text not null,
  source_revision text not null,
  framework text not null,
  license text,
  manifest jsonb not null,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (num_nonnulls(owner_profile_id, owner_organization_id) = 1)
);

create table public.hardware_profiles (
  id uuid primary key default gen_random_uuid(),
  slug text not null,
  robot_family text not null,
  manufacturer text,
  configuration jsonb not null,
  created_by uuid not null references public.profiles(id),
  created_at timestamptz not null default now()
);

create table public.benchmarks (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  version text not null,
  protocol jsonb not null,
  source_url text,
  created_by uuid not null references public.profiles(id),
  published_at timestamptz,
  created_at timestamptz not null default now(),
  unique (slug, version)
);

create table public.evaluations (
  id uuid primary key default gen_random_uuid(),
  skill_id uuid not null references public.skills(id),
  hardware_profile_id uuid not null references public.hardware_profiles(id),
  benchmark_id uuid not null references public.benchmarks(id),
  submitted_by uuid not null references public.profiles(id),
  verification_status public.verification_status not null default 'self_tested',
  visibility public.evaluation_visibility not null default 'public',
  success_rate numeric(5,2) check (success_rate between 0 and 100),
  trial_count integer not null check (trial_count > 0),
  reproduction_count integer not null default 0 check (reproduction_count >= 0),
  runtime jsonb not null,
  evidence jsonb not null default '[]'::jsonb,
  result_digest text not null,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  unique (skill_id, hardware_profile_id, benchmark_id, result_digest)
);

create index evaluations_skill_idx on public.evaluations(skill_id);
create index evaluations_hardware_idx on public.evaluations(hardware_profile_id);
create index evaluations_published_idx on public.evaluations(published_at desc) where visibility = 'public';

create view public.evaluation_summaries with (security_invoker = true) as
select
  e.id,
  s.slug,
  s.name as skill_name,
  coalesce(o.name, p.display_name, p.handle, 'Independent contributor') as author_name,
  h.robot_family,
  s.framework,
  e.success_rate,
  e.trial_count,
  e.reproduction_count,
  e.verification_status,
  e.published_at
from public.evaluations e
join public.skills s on s.id = e.skill_id
join public.hardware_profiles h on h.id = e.hardware_profile_id
left join public.organizations o on o.id = s.owner_organization_id
left join public.profiles p on p.id = s.owner_profile_id
where e.visibility = 'public' and e.published_at is not null and s.published_at is not null;

alter table public.profiles enable row level security;
alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.skills enable row level security;
alter table public.hardware_profiles enable row level security;
alter table public.benchmarks enable row level security;
alter table public.evaluations enable row level security;

create policy "Public profiles are readable" on public.profiles for select using (true);
create policy "Users create own profile" on public.profiles for insert with check (auth.uid() = id);
create policy "Users update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "Organizations are readable" on public.organizations for select using (true);
create policy "Users create organizations" on public.organizations for insert with check (auth.uid() = created_by);
create policy "Organization memberships readable" on public.organization_members for select using (true);

create policy "Published skills are readable" on public.skills for select using (published_at is not null or owner_profile_id = auth.uid());
create policy "Users create own skills" on public.skills for insert with check (owner_profile_id = auth.uid());
create policy "Owners update own skills" on public.skills for update using (owner_profile_id = auth.uid()) with check (owner_profile_id = auth.uid());

create policy "Hardware profiles are readable" on public.hardware_profiles for select using (true);
create policy "Users create hardware profiles" on public.hardware_profiles for insert with check (created_by = auth.uid());
create policy "Benchmarks are readable" on public.benchmarks for select using (published_at is not null or created_by = auth.uid());
create policy "Users create benchmarks" on public.benchmarks for insert with check (created_by = auth.uid());

create policy "Public evaluations and own evaluations readable" on public.evaluations for select using (visibility = 'public' or submitted_by = auth.uid());
create policy "Users submit evaluations" on public.evaluations for insert with check (submitted_by = auth.uid());
create policy "Submitters update unpublished evaluations" on public.evaluations for update using (submitted_by = auth.uid() and published_at is null) with check (submitted_by = auth.uid());

grant select on public.evaluation_summaries to anon, authenticated;

insert into storage.buckets (id, name, public, file_size_limit)
values ('evaluation-evidence-public', 'evaluation-evidence-public', true, 536870912),
       ('evaluation-evidence-private', 'evaluation-evidence-private', false, 536870912)
on conflict (id) do nothing;

create policy "Public evaluation evidence readable" on storage.objects for select using (bucket_id = 'evaluation-evidence-public');
create policy "Authenticated users upload evidence" on storage.objects for insert to authenticated with check (
  bucket_id in ('evaluation-evidence-public', 'evaluation-evidence-private') and (storage.foldername(name))[1] = auth.uid()::text
);
