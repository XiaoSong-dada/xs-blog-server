-- public.friendship_link definition

-- Drop table

-- DROP TABLE public.friendship_link;

CREATE TABLE public.friendship_link (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	"name" varchar(100) NULL,
	url varchar(255) NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	description text NULL,
	logo_url varchar(500) NULL,
	sort_order int4 NULL,
	is_active bool DEFAULT true NULL,
	CONSTRAINT friendship_link_pk PRIMARY KEY (id)
);