document.getElementById("lightSlider").addEventListener("input", function () {
    document.getElementById("lightValue").innerText = this.value + "%";
});

document.getElementById("soundThresholdSlider").addEventListener("input", function () {
    document.getElementById("soundThresholdValue").innerText = this.value + "%";
});

async function ForceOnRelay() {
    const request = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    await fetch("http://192.168.1.25:5000/force_relay_on", request);  // Envoie au serveur Flask pour appeler ROS2
    fetchStateRelay();  // Mise à jour immédiate de l'état du relais
}

async function ForceOffRelay() {
    const request = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    await fetch("http://192.168.1.25:5000/force_relay_off", request);  // Envoie au serveur Flask pour appeler ROS2
    fetchStateRelay();  // Mise à jour immédiate de l'état du relais
}

async function UnforceRelay() {
    const request = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    await fetch("http://192.168.1.25:5000/unforce_relay", request);  // Envoie au serveur Flask pour appeler ROS2
    fetchStateRelay();  // Mise à jour immédiate de l'état du relais
}

async function fetchStateRelay() {
    const response = await fetch("http://192.168.1.25:5000/get-state-relay"); // adresse local pour le moment à modifier plus tard
    const data = await response.json();
    const state_relay = data.state_relay;
    const relayStatusElement = document.getElementById("relayStatus")

    if (state_relay == 1){
        relayStatusElement.classList.remove('status-off');
        relayStatusElement.classList.add('status-on');
    }
    else{
        relayStatusElement.classList.remove('status-on');
        relayStatusElement.classList.add('status-off');
    }
}

async function fetchThresholds() {
    const response = await fetch("http://192.168.1.25:5000/get_thresholds"); // adresse local pour le moment à modifier plus tard
    const data = await response.json();
    //console.log("Données reçues du serveur:", data); // DEBUG

    const thresholds_lum = data.luminosity_threshold.toString();
    const thresholds_sound = data.sound_threshold.toString(); 
    document.getElementById("currentLightThreshold").innerText = thresholds_lum + "%";
    document.getElementById("currentSoundThreshold").innerText = thresholds_sound + "%";

}


document.getElementById("sendThresholdsButton").addEventListener("click", async function () {
    const lightThreshold = document.getElementById("lightSlider").value;
    const soundThreshold = document.getElementById("soundThresholdSlider").value;

    // Envoie des deux valeurs en une seule requête
    await updateThresholds(lightThreshold, soundThreshold);
});

async function updateThresholds(lightThreshold, soundThreshold) {
        // Envoi d'un seul objet contenant les deux valeurs
        const response = await fetch('http://192.168.1.25:5000/update_thresholds', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',  // Indiquer que le corps de la requête est en JSON
            },
            body: JSON.stringify({ 
                luminosity_threshold: parseInt(lightThreshold), 
                sound_threshold: parseInt(soundThreshold) 
            })  // Formater les données en JSON
        });

}



// Event listener pour les boutons
document.getElementById("forceRelayOnButton").addEventListener("click", ForceOnRelay);
document.getElementById("forceRelayOffButton").addEventListener("click", ForceOffRelay);
document.getElementById("unforceRelayButton").addEventListener("click", UnforceRelay);

setInterval(fetchThresholds, 1000)
setInterval(fetchStateRelay, 1000)
