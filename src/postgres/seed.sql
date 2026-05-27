INSERT INTO horario
(asignatura, profesor, grupo, aula, hora_inicio, hora_fin, dia_semana)
VALUES

-- LUNES
('CED', 'Gemma Sanchez Anton', '1-1', 'G1.32', '08:30', '10:20', 1),
('CED', 'Francisco Perez Garcia', '1-1', 'G1.35', '08:30', '10:20', 1),

('CIN', 'Delia Garijo Royo', '1-1', 'A0.12', '10:40', '12:30', 1),
('CIN', 'Delia Garijo Royo', '1-1', 'B1.31', '10:40', '12:30', 1),
('CIN', 'Emmanuel Jean Briand', '1-1', 'B1.32', '10:40', '12:30', 1),
('CIN', 'Jose Maria Ucha Enriquez', '1-1', 'B2.30', '10:40', '12:30', 1),

('CED', 'Francisco Perez Garcia', '1-1', 'A0.12', '12:40', '14:30', 1),
('CED', 'Gemma Sanchez Anton', '1-1', 'G1.32', '12:40', '14:30', 1),
('CED', 'Francisco Perez Garcia', '1-1', 'G1.35', '12:40', '14:30', 1),

-- MARTES
('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'G0.34', '08:30', '10:20', 2),
('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'G0.34', '08:30', '10:20', 2),

('IMD', 'Amparo Osuna Lucena', '1-1', 'A0.12', '10:40', '12:30', 2),

('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'A0.12', '12:40', '14:30', 2),
('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'G0.34', '12:40', '14:30', 2),
('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'G0.34', '12:40', '14:30', 2),
('FFI', 'Vicente Losada Torres', '1-1', 'G0.35', '12:40', '14:30', 2),
('FFI', 'Vicente Losada Torres', '1-1', 'G0.35', '12:40', '14:30', 2),

-- MIERCOLES
('CED', 'Francisco Perez Garcia', '1-1', 'G1.32', '08:30', '10:20', 3),

('FP', 'David Felipe Benavides Cuevas', '1-1', 'A0.12', '10:40', '12:30', 3),
('FP', 'Jose Angel Galindo Duarte', '1-1', 'F1.31', '10:40', '12:30', 3),
('FP', 'Belen Vega Marquez', '1-1', 'F1.32', '10:40', '12:30', 3),
('FP', 'Pablo Reina Jimenez', '1-1', 'F1.33', '10:40', '12:30', 3),

('CIN', 'Delia Garijo Royo', '1-1', 'A0.12', '12:40', '14:30', 3),

-- JUEVES
('IMD', 'Amparo Osuna Lucena', '1-1', 'A0.12', '08:30', '10:20', 4),
('IMD', 'Amparo Osuna Lucena', '1-1', 'B1.31', '08:30', '10:20', 4),
('IMD', 'Maria Magdalena Fernandez Lebron', '1-1', 'B1.32', '08:30', '10:20', 4),
('IMD', 'Maria Dolores Frau Garcia', '1-1', 'B1.33', '08:30', '10:20', 4),

('CED', 'Francisco Perez Garcia', '1-1', 'A0.12', '10:40', '12:30', 4),

('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'A0.12', '12:40', '14:30', 4),

-- VIERNES
('FFI', 'Gonzalo Plaza Valtueña', '1-1', 'A0.12', '10:40', '12:30', 5),

('FP', 'David Felipe Benavides Cuevas', '1-1', 'A0.12', '12:40', '14:30', 5);

INSERT INTO sensor
(sensor_id, tipo, validez)
VALUES
('tem', 'hibrido', 60*30),
('son', 'hibrido', 60*1),
('luz', 'hibrido', 60*5),
('hum', 'ambiental', 60*20),
('vib', 'alarma', 60*10),
('gas', 'alarma', 60*10);