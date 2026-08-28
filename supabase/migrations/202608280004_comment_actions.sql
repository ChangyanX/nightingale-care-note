begin;

alter table public.comments
add column deleted_at timestamptz,
add column deleted_by uuid references public.profiles(id) on delete restrict,
add constraint comments_deletion_consistent check (
  (deleted_at is null and deleted_by is null)
  or (deleted_at is not null and deleted_by = author_id)
);

create function public.delete_own_comment(p_comment_id uuid)
returns public.comments
language plpgsql
security definer
set search_path = ''
as $$
declare
  target public.comments;
begin
  select * into target
  from public.comments
  where id = p_comment_id;

  if not found then
    raise exception using errcode = 'P0002', message = 'Comment not found';
  end if;

  if target.author_id <> auth.uid()
     or not public.has_clinic_role(
       target.clinic_id,
       array['staff', 'clinician']::public.clinic_role[]
     ) then
    raise exception using errcode = '42501', message = 'Only the author can delete this comment';
  end if;

  if target.deleted_at is null then
    delete from public.mentions where comment_id = target.id;
    delete from public.comment_assignees where comment_id = target.id;
    delete from public.comment_reactions where comment_id = target.id;

    update public.comments
    set body = '[Comment deleted by author]',
        body_format = 'plain',
        status = 'resolved',
        resolved_at = coalesce(resolved_at, now()),
        assigned_to = null,
        source_version_id = null,
        source_start_offset = null,
        source_end_offset = null,
        quoted_text = null,
        deleted_at = now(),
        deleted_by = auth.uid()
    where id = target.id
    returning * into target;
  end if;

  return target;
end;
$$;

revoke all on function public.delete_own_comment(uuid) from public, anon;
grant execute on function public.delete_own_comment(uuid) to authenticated;

drop policy optional_clinical_reactions on public.comment_reactions;
create policy comment_reactions_select_clinical
on public.comment_reactions for select to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician', 'admin']::public.clinic_role[]
  )
);
create policy comment_reactions_insert_own
on public.comment_reactions for insert to authenticated
with check (
  profile_id = auth.uid()
  and public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
);
create policy comment_reactions_delete_own
on public.comment_reactions for delete to authenticated
using (
  profile_id = auth.uid()
  and public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
);

alter table public.comment_reactions replica identity full;
alter publication supabase_realtime add table public.comment_reactions;

commit;
