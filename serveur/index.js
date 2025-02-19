const sqlite3 = require('sqlite3');
const express = require("express");
const cors = require("cors"); // Pour autoriser les requêtes de l'extérieur

sqlite3.verbose();

const dbname = 'database.db3';

const app = express();
const port = 3000;

app.use(cors()); //Pas de restriction d'origine

app.get('/all', (req, res) => {
    const db = new sqlite3.Database(dbname);
    const requete_user = req.query;
    
    console.log(requete_user);

    const QUERY = `SELECT * FROM sensor_data`;

    console.log(QUERY);

    db.serialize(() => {
        db.all(QUERY, [], (erreur, montableau) => {
            if (erreur) {
                throw erreur;
            }
            res.json(montableau);
            //console.log(montableau);  // Utilisation de `valeur` avec minuscule
            db.close();
        });
    });
});

app.get('/LastValue', (req, res) => {
    const db = new sqlite3.Database(dbname);
    const requete_user = req.query;
    
    console.log(requete_user);

    const QUERY = `SELECT * FROM sensor_data ORDER BY data_id DESC LIMIT 1`;

    console.log(QUERY);

    db.serialize(() => {
        db.all(QUERY, [], (erreur, montableau) => {
            if (erreur) {
                throw erreur;
            }
            res.json(montableau);
            //console.log(montableau);  // Utilisation de `valeur` avec minuscule
            db.close();
        });
    });
});


app.get('/fiveLastValue', (req, res) => {
    const db = new sqlite3.Database(dbname);
    const requete_user = req.query;
    
    console.log(requete_user);

    const QUERY = `SELECT * FROM sensor_data ORDER BY data_id DESC LIMIT 5`;

    console.log(QUERY);

    db.serialize(() => {
        db.all(QUERY, [], (erreur, montableau) => {
            if (erreur) {
                throw erreur;
            }
            res.json(montableau);
            //console.log(montableau);  // Utilisation de `valeur` avec minuscule
            db.close();
        });
    });
});

app.listen(port, () => {
    console.log(`Le serveur écoute le port : ${port}!`);
});
