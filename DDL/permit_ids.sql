-- public.permit_ids definition

-- Drop table

-- DROP TABLE public.permit_ids;

CREATE TABLE public.permit_ids (
	serverid int8 NOT NULL,
	userid _int8 NULL,
	CONSTRAINT permit_ids_pkey PRIMARY KEY (serverid)
);