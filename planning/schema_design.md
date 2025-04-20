🧠 Unified Graph Schema from Parsed Output
🔹 1. Core Node Types

Node Label	Attributes	Example
Concept	name, source	"Airway Cell Function"
Label	text, type, justification	"Defense Mechanism"
Rule	id, confidence	id: 7, confidence: 75
OntologyClass	name, iri, superclass	:Neuron, subclassOf :SpecializedCell
Property	name, type, domain, range	hasSpecializedProtein
Individual	name, class, function	:neuron, :Neuron, "transmitting signals"
Corpus	filename, source_type	"cell_handout.pdf", "PDF"
🔸 2. Core Relationships (Edges)

Edge Type	From → To	Notes
:HAS_LABEL	Concept → Label	Links label to a concept
:JUSTIFIED_BY	Label → Concept	Justification lives on label or edge
:PREREQUISITE_FOR	Concept → Concept	Derived from Rule IF→THEN
:SUPPORTS_RULE	Rule → Concept (both if and then)	Two edges per rule
:IN_CORPUS	Any → Corpus	Where the entity was extracted
:INSTANCE_OF	Individual → OntologyClass	e.g., :leafCell → :LeafCell
:USES_PART	Individual → SpecializedPart	:neuron → :Axon
:USES_PROTEIN	Individual → SpecializedProtein	:rootCell → :WaterChannels
:DEFINED_BY	OntologyClass/Property → Corpus	Tracks original source

🛠️ Parser Design
🔹 Input Files
label_suggestions.txt: JSON array of { concept, labels[], justification }

ontology.txt: TTL-formatted OWL ontology

rules.txt: JSON array of { id, if, then, confidence }

🔸 Output (Neo4j-compatible objects or RDF triples)
You’ll want to:

Normalize all concept names to slugified URIs or camelCase

Decompose multi-condition rules (e.g., "Microvilli AND Nutrient Transporters") into separate concept links

Tag all outputs with source filename to support traceability

🧬 JSONL Intermediate Format Example (per concept)
json
Copy
Edit
{
  "concept": "Neuron",
  "labels": [
    {
      "text": "Signal Transmission",
      "type": "Descriptive",
      "justification": "Neurons convey signals and facilitate communication..."
    },
    ...
  ],
  "rules_if": [3],
  "rules_then": [],
  "from_ontology": true,
  "from_corpus": "label_suggestions.txt"
}
