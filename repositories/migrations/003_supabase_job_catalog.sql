CREATE TABLE IF NOT EXISTS public.jobs (
    id text PRIMARY KEY,
    title text NOT NULL,
    description text NOT NULL DEFAULT '',
    required_skills jsonb NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(required_skills) = 'array'),
    location text NOT NULL DEFAULT '',
    application_url text NOT NULL DEFAULT '',
    source text NOT NULL,
    updated_at date NOT NULL,
    active boolean NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_jobs_active_updated
    ON public.jobs (active, updated_at DESC);

ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.jobs FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.jobs TO service_role;

CREATE OR REPLACE FUNCTION public.replace_job_catalog(p_jobs jsonb)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF jsonb_typeof(p_jobs) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'p_jobs must be a JSON array';
    END IF;
    IF jsonb_array_length(p_jobs) = 0 THEN
        RAISE EXCEPTION 'p_jobs must not be empty';
    END IF;

    DELETE FROM public.jobs WHERE id IS NOT NULL;

    INSERT INTO public.jobs (
        id, title, description, required_skills, location,
        application_url, source, updated_at, active
    )
    SELECT
        item->>'id',
        item->>'title',
        COALESCE(item->>'description', ''),
        COALESCE(item->'required_skills', '[]'::jsonb),
        COALESCE(item->>'location', ''),
        COALESCE(item->>'application_url', ''),
        item->>'source',
        (item->>'updated_at')::date,
        COALESCE((item->>'active')::boolean, true)
    FROM jsonb_array_elements(p_jobs) AS item;
END;
$$;

REVOKE ALL ON FUNCTION public.replace_job_catalog(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.replace_job_catalog(jsonb) TO service_role;
