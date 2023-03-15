# Rigid Packer
### Hierarchical Circle Packing with Real Time Dynamics

<img src='screen.png' alt='Screenshot' width='100%'>

<img src='demo.gif' alt='Demonstration' width='185' align='right' float='left'>

## Requirements
* Python 3.7
* pybox2d
* PyQt5
* pygame

## Setup
1. create an *inventory.db* SQLite file with the following schema:
	```SQL
	CREATE TABLE "item" (
		"item_id"	INTEGER NOT NULL UNIQUE,
		"name"	TEXT NOT NULL UNIQUE,
		"product_name"	TEXT,
		PRIMARY KEY("item_id" AUTOINCREMENT)
	);
	CREATE TABLE "placement" (
		"placement_id"	INTEGER NOT NULL UNIQUE,
		"arrangement_id"	INTEGER NOT NULL,
		"item_id"	INTEGER NOT NULL UNIQUE,
		"parent_id"	INTEGER,
		FOREIGN KEY("parent_id") REFERENCES "item"("item_id"),
		FOREIGN KEY("item_id") REFERENCES "item"("item_id"),
		PRIMARY KEY("placement_id" AUTOINCREMENT),
		FOREIGN KEY("arrangement_id") REFERENCES "arrangement"("arrangement_id")
	);
	CREATE TABLE "arrangement" (
		"arrangement_id"	INTEGER NOT NULL UNIQUE,
		"name"	TEXT NOT NULL UNIQUE,
		PRIMARY KEY("arrangement_id" AUTOINCREMENT)
	);
	```
1. add row with “current” value of *name* field to the *arrangement* table
1. fill the database with any data
1. put the *inventory.db* file next to the app’s folder

## Using
1. run *main.pyw*
1. press `Space` to stop/run engine
1. press `Escape` to quit
