title:	Fix: Imperfezioni Grafiche e Visual Bug
state:	OPEN
author:	Francespo
labels:	
comments:	0
assignees:	
projects:	
milestone:	
number:	6
--
# Imperfezioni Grafiche e Visual Bug

Questo branch mira a risolvere sovrapposizioni, duplicazioni e disallineamenti UI sparsi nelle pagine.

## Fix necessari:
1. **Paginazione Duplicata:**
   - Il componente (es. "Page 1 of X") appare due volte (Squadrons, Lists).
   - *Azione:* Rimuovere il rendering condizionale duplicato del componente di paginazione.
2. **Dashboard Spacing:**
   - Sovrapposizioni tra il testo "RANGE" e la data dei filtri in alto.
   - *Azione:* Aggiungere padding appropriato per separare correttamente il titolo e i metadati.
3. **Eccesso di Filtri Visibili:**
   - In alcune pagine compaiono "TOURNAMENT" e "SQUADRON" filters assieme, creando confusione.
   - *Azione:* Filtrare quali blocchi mostrare o racchiuderli in componenti Accordion compatti.
4. **Icone e Counter disallineati:**
   - Nelle card (Squadrons), l'icona nave ├¿ minuscola e il numero count ("2x") ├¿ disallineato.
   - *Azione:* Aumentare la dimensione dell'icona e allineare al centro (align-items: center).

