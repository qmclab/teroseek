async function getTeromolResult(userQuestion) {
    // Show loading state
    document.getElementById('teromolResult').innerHTML = '<span class="loading">正在加载... <span class="typing"></span></span>';
    try {
        const response = await fetch('/chat/api/get_teromol', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: userQuestion })
        });
        const data = await response.json();
        console.log(data);
        
        // Update Teromol results
        const teromolElement = document.getElementById('teromolResult');
        teromolElement.innerHTML = ''; // Clear previous content
        
        if ('teromol' in data && Array.isArray(data.teromol) && data.teromol.length > 0) {
            // Create a table to structure the data
            const table = document.createElement('table');

            data.teromol.forEach(molecule => {
                const row = document.createElement('tr');
                
                const propertiesCell = document.createElement('td');
                propertiesCell.className = 'properties';
                propertiesCell.innerHTML = `
                    <strong>ID:</strong> <a href="http://terokit.qmclab.com/molecule.html?MolId=${molecule.tkc_id}" target="_blank">${molecule.tkc_id}</a><br>
                    <strong>Name:</strong> ${molecule.mol_name}<br>
                    <strong>SMILES:</strong> <span class="smiles">${molecule.smi}</span><br>
                `;
                
                const imageCell = document.createElement('td');
                imageCell.className = 'image';
                imageCell.innerHTML = `${molecule.svg}`;
                
                row.appendChild(propertiesCell);
                row.appendChild(imageCell);
                table.appendChild(row);
            });
            
            teromolElement.appendChild(table);
        } else {
            teromolElement.textContent = '';
        }
    } catch (error) {
        console.error('获取结果出错:', error);
        document.getElementById('teromolResult').textContent = '';
    }
}




