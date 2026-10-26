INSERT INTO categories(slug,name,description) VALUES
('structural','Structural Materials','Cement, steel, blocks and structural essentials'),
('exterior','Exterior & Roofing','Exterior finishes, protection and roofing'),
('interior','Interior Finishes','Tiles, finishes, paint and interiors'),
('electrical','Electrical','Wiring, switches, lighting and distribution'),
('plumbing','Plumbing & Sanitary','Pipes, valves, sanitary and drainage'),
('tools','Tools & Hardware','Site tools, fixing and accessories')
ON CONFLICT(slug) DO NOTHING;
INSERT INTO products(slug,name,category,unit,description,specification,image_key) VALUES
('opc-cement','Ordinary Portland Cement','structural','bag','General cement for applications specified by a professional.','Grade and certification require supplier verification','cement'),
('tmt-rebar','Reinforcement Steel Bar','structural','kg','Reinforcing steel for professionally designed concrete work.','Diameter and grade selected per design','steel'),
('concrete-block','Concrete Masonry Block','structural','piece','Masonry block for appropriate wall assemblies.','Density and dimensions vary by supplier','block'),
('roofing-sheet','Metal Roofing Sheet','exterior','sheet','Metal sheet roofing for suitable roof systems.','Gauge, coating, profile, span to verify','roof'),
('exterior-paint','Exterior Weatherproof Paint','exterior','litre','Exterior coating for compatible surfaces.','Product data sheet required','paint'),
('ceramic-floor-tile','Ceramic Floor Tile','interior','m²','Flooring tile for suitable indoor areas.','Slip rating and thickness vary','tile'),
('gypsum-board','Gypsum Board','interior','sheet','Interior wall and ceiling board.','Fire and moisture grades vary','board'),
('electrical-cable','Electrical Cable','electrical','metre','Electrical installation cable.','Cross-section and insulation class must be designed','wire'),
('modular-switch','Modular Wall Switch','electrical','piece','Electrical wall switch from approved suppliers.','Rating and certification to verify','switch'),
('pvc-pipe','PVC Pipe','plumbing','metre','Pipe for specified water or drainage systems.','Diameter and pressure class depend on application','pipe'),
('sanitary-basin','Wash Basin','plumbing','piece','Bathroom wash basin for residential and commercial spaces.','Dimensions and mounting vary','basin'),
('safety-helmet','Construction Safety Helmet','tools','piece','Protective helmet for appropriate site activities.','Certification and fit required','helmet')
ON CONFLICT(slug) DO NOTHING;
