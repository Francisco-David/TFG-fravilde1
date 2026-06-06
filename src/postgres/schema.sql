-- -- sso not like this --
-- SELECT employees.emp_name
--      , departments.dept_name
--      , ...
-- instead, provide the distinction with column aliases like this --

-- SELECT employees.name AS emp_name
--      , departments.name AS dept_name

CREATE TYPE nivel_alerta AS ENUM ('ALARMA', 'AVISO', 'OK');
CREATE TYPE estado_sesion AS ENUM ('en_curso', 'finalizada');
CREATE TYPE tipo_sensor AS ENUM ('ambiental', 'alarma', 'mixto');
CREATE TYPE estado_sensor AS ENUM ('operativo', 'defectuoso');

CREATE TABLE sensor (
    sensor_id VARCHAR(3) PRIMARY KEY,
        -- Mejor no usar CHECK para validar el sensor_id, ya que si en el futuro se añaden nuevos tipos de sensores
        -- CHECK (sensor_id IN ('tem', 'hum', 'vib', 'son', 'gas', 'luz')),
    tipo tipo_sensor NOT NULL,
    validez INTEGER NOT NULL,
    estado estado_sensor NOT NULL DEFAULT 'operativo'
);

CREATE TABLE horario (
    horario_id SERIAL PRIMARY KEY,
    asignatura TEXT NOT NULL,
    profesor TEXT,
    grupo VARCHAR(3) CHECK (grupo ~ '^[0-9]-[0-9]$'),  -- Grupo clase (ej. 1-1, 1-2, 2-1)
    aula VARCHAR(5) NOT NULL CHECK (aula ~ '^[A-Za-z][0-9]\.[0-9]{2}$'), 
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    dia_semana SMALLINT NOT NULL CHECK (dia_semana BETWEEN 1 AND 7) 
);

CREATE TABLE sesion (
    sesion_id SERIAL PRIMARY KEY,
    horario_id INTEGER REFERENCES horario(horario_id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    comienza TIME,
    finaliza TIME,
    estado estado_sesion NOT NULL DEFAULT 'en_curso'    
);

CREATE TABLE lectura (
    lectura_id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(3) REFERENCES sensor(sensor_id) ON DELETE SET NULL,
    valor REAL NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT now(),
    sesion_id INTEGER REFERENCES sesion(sesion_id) ON DELETE SET NULL
);

CREATE TABLE alerta (
    alerta_id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(3) REFERENCES sensor(sensor_id) ON DELETE SET NULL,
    tipo TEXT NOT NULL,
    nivel nivel_alerta NOT NULL DEFAULT 'AVISO',     
    timestamp TIMESTAMP NOT NULL DEFAULT now(),
    reconocida BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE evaluacion (
    evaluacion_id SERIAL PRIMARY KEY,
    sesion_id  INTEGER REFERENCES sesion(sesion_id) ON DELETE SET NULL,
    puntuacion TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT now()
);
