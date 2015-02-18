.mode csv
.import dec.csv voters
ALTER TABLE voters ADD COLUMN vote;
ALTER TABLE voters ADD COLUMN confirmed;
