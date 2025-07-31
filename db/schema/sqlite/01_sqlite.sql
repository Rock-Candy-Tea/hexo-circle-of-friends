CREATE TABLE friends (
	id INTEGER NOT NULL, 
	name VARCHAR(256), 
	link VARCHAR(1024), 
	avatar VARCHAR(1024), 
	error BOOLEAN, 
	"createdAt" VARCHAR(1024), 
	PRIMARY KEY (id)
);

CREATE TABLE posts (
	id INTEGER NOT NULL, 
	title VARCHAR(256), 
	created VARCHAR(256), 
	updated VARCHAR(256), 
	link VARCHAR(1024), 
	author VARCHAR(256), 
	avatar VARCHAR(1024), 
	rule VARCHAR(256), 
	"createdAt" VARCHAR(1024), 
	PRIMARY KEY (id)
);

CREATE TABLE article_summaries (
	id INTEGER NOT NULL,
	link VARCHAR(256) NOT NULL,
	content_hash VARCHAR(64) NOT NULL,
	summary TEXT,
	ai_model VARCHAR(128),
	"createdAt" VARCHAR(1024),
	"updatedAt" VARCHAR(1024),
	PRIMARY KEY (id),
	UNIQUE (link)
);