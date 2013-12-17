#!/usr/bin/env python
# -*- coding: Windows-1252 -*- 
import sys 
from factory import ManifestFactory

msref = "add_ms_10289"

fac = ManifestFactory()
fac.set_base_metadata_uri("http://sanddragon.bl.uk/IIIFMetadataService/")
fac.set_base_image_uri("http://sanddragon.bl.uk/IIIFImageService/")

fac.set_iiif_image_conformance(1.1, 2) # Version, ComplianceLevel
fac.set_debug("warn") # 'error' will turn off warnings

manifest = fac.manifest(ident="add_ms_10289", label="Add MS 10289")

mddate = u'1275 - 1300'.encode('utf-8')
mdtitle = "Li Romanz du Mont Saint-Michel, a miscellany of romances, moralistic and religious texts and medical recipes"
mdlocation = "British Library"
mdcontents = u"Contents:   ff. 1r-64r: Guillaume de Saint Pair or Guillelme de Seint Paier, Li romanz du Mont Saint Michel or Roman de Mont Saint Michel, incipit, 'Molz pelerins qui vunt al munt', explicit, 'Longue de corne ou il est mis'.  ff. 64r-81v: Andreu de Costances, Une estoire de la resurrection de Jesu Crist, or Verse Gospel of Nicodemus in verse, incipit, 'Seignors mestre Andreu de costances..', explicit, 'Les boens mist hors lessa les maux';  f. 81v: Recipe for a lotion to whiten the skin, incipit, 'Ogneme[n]t espue por blanchir';  ff. 82r-121r: Roman de la destruction de Jerusalem or Le livre de Titus ou de Vespasian, a chanson de geste, incipit, 'Seignors or entende chevalier seriant', explicit, 'nel doit len pas mescroire';  ff. 122r-129r: Medical recipes or Secrets de medecine, incipit 'A la dolor deu chief polieul cuit..', explicit, 'tant q[ue] il sue cest ce qui plus vaut'.  f. 129v: De saint Nicaise, in Latin, incipit 'Sanctus Nichasius habuit mac[u]lam in oculo';  ff. 129v-132v: André or Andreu de Costances: Le romanz des Franceis or Arflet, incipit, 'Reis arflet de nohundrelande', explicit, 'Q[ue]r p[ar]tot dit veir cest la fin.';  f. 132v: List of twelve pairs of France, incipit, 'Dux burgondie';  ff. 133r-172r: Petrus Alphonsus: Fables, a French translation of the Disciplina Clericalis entitled Chatoiment d'un pere a son fils, incipit, 'Qui veut henor eu siecle aveir', explicit, 'Garni le tienge en son vivant';  ff. 172r-175r: Robert de Blois, Compendium Amoris, extracts from Chastoiement des Dames, incipit,'[M]einte gent parolent damors', explicit, 'lor veut dex li dont honte ame';  ff. 175v-178v: Colin Malet: Fabliau de Juglet or Jouglet, incipit, 'Jadis en coste mon ferrant', explicit, 'Q[ue] assez miez [con]chie lui'.  Decoration:   A historiated initial in colours with frame in red of two pilgrims with staffs (f. 1r). An ink drawing in brown of the church of Mont Saint Michel burning with flames in red (f. 45v). Two puzzle initials in red and blue with penwork decoration (ff. 82r,133r). Initials in blue with penwork decoration in red or in red with penwork decoration in blue at the beginning of chapters. Small initials in blue or red at the beginning of lines, some with pen-flourishing in blue; line fillers in red or blue (ff. 1r-64v). Paraphs in red or blue. Rubrics in red."
mdlanguages = "Old French, Anglo-Norman, Latin"
mdphysical = "Materials: Parchment. Dimensions: 190 x 135mm (written space: 145 x 75/110mm). Foliation: ff. 179 (f. 179 is a parchment flyleaf fragment + 4 unfoliated paper flyleaves at the beginning and at the end). Script: Gothic, written above the top line. Layout: Parts written in two columns. Binding: BM/BL in-house. Rebound in 1959."
mdownership = u"Origin: France, N.W. (Normandy). Provenance: The abbey of Mont Saint-Michel, dated ?1280: inscribed 'anno octog[esimo]', (f. 64r); a 15th-century ownership inscription, 'Iste liber est de thesauraria montis' is in the outer margin of f. 1r. Jaques Cujas, humanist scholar and legal expert (b. 1529, d. 1590), perhaps taken by him, as authorised by Nicolas le Fevre on behalf of Louis XIII, from the abbey library in c.1582 (see Genevieve Nortier, Les bibliotheques médiévales des abbayes bénédictines de Normandie (Caen: Caron et cie, 1966), p. 151); his books were dispersed at his death and this manuscript may have returned to the abbey then.In the 1739 catalogue of the abbey of Mont Saint Michel: see Bernard de Montfaucon, Bibliotheca bibliothecarum manuscriptorum nova, 2 vols (1739), II, p. 1360), no. 216: 'Histoire du Mont St Michel en vers, faite du temps de l'Abbé Robert de Torigny' (r. 1154-1186). In 1799 the manuscripts of the abbey library were moved to Avranches, but a number were lost. The present manuscript was removed from the collection between 1799 and 1835, when the first inventory was made in Avranches.Richard Heber, landowner and book collector (b.1773, d. 1833), probably bought by him in Europe in the early 18th century; his sale, 20 February 1836, lot 1702; purchased by the British Museum."
mdbibliography = u"Catalogue of Additions to the Manuscripts in the British Museum in the Years 1836-1846 (London: British Museum, 1843), p. 27. H. L. D. Ward and J. A. Herbert, Catalogue of Romances in the Department of Manuscripts in the British Museum, 3 vols (London: British Museum, 1883-1910), I (1883), pp. 179-80, 812-13; II (1893), pp. 259-65. John Howard Fox, Robert de Blois, son oeuvre didactique et narrative. Étude linguistique et littéraire suivie d'une édition critique avec commentaire et glossaire de 'l'Enseignement des princes' et du 'Chastoiement des dames' (Paris: Nizet, 1950), [an edition of the text, ff. 172-175r]. Anthony J. Holden, 'Le Roman des Franceis' in Etudes de langue et de littérature du moyen age: Offertes à Felix Lecoy (Paris: Honoré Champion, 1973), pp. 213-33 (p. 214). Félix Lecoy, 'À propos du Romanz des Franceis d'André de Coutances', Phonétique et linguistique romanes. Mélanges offerts à M. Georges Straka, Revue de linguistique romane, 34, (1970), pp. 123-25. R. Graham Birrell, 'Regional vocabulary in Le Roman du Mont Saint-Michel', Romania, 100 (1979), 260-70 (p. 261). Willem Noomen, 'Auteur, narrateur, récitant de fabliaux, le témoignage des prologues et des épilogues', Cahiers de civilisation médiévale, 35 (1992), 313-50 (pp. 321-22). Ruth Dean and Maureen Bolton, Anglo-Norman Literature, A Guide to Texts and Manuscripts (London: Anglo-Norman Text Society, 1999), nos. 220.1, 501r. Le Jongleur par lui-meme: Choix de dits et de fabliaux, ed. by Willem Noomen (Louvain: Peeters, 2003), pp. 276-311 [includes an edition of the text on ff. 175-178]. Lydie Lansard, 'De l'Évangile de Nicodème au Roman de la Résurrection d'André de Coutances', Apocrypha, 16, (2005), pp. 229-51. Le Roman du Mont Saint-Michel (xiie siècle), ed. by Catherine Bougy, Les manuscrits de Mont Saint Michel, Textes fondateurs, 2 vols (Avranches: Presses Universitaires de Caen, 2009), II, pp. 43-45, pl. I-IV, VI-IX, XI,XII [contains a description and edition of ff. 1-64], online at http://www.unicaen.fr/services/puc/sources/gsp/index.php?page=sommaire [accessed 05.11.2013]. Lydie Lansard and Laurent Brun, 'London, British Library Additional 10289', Arlima, Archives de littérature du Moyen Age (University of Ottawa, 2010) at http://www.arlima.net/mss/united_kingdom/london/british_library/additional/010289.html [accessed 15.11.2013]."

manifest.set_metadata({"Date": mddate, "Title": mdtitle, "Location": mdlocation,"Contents": mdcontents, "Languages": mdlanguages, "Physical Description": mdphysical, "Ownership": mdownership, "Bibliography": mdbibliography})
manifest.description = "Li Romanz du Mont Saint-Michel, a miscellany of romances, moralistic and religious texts and medical recipes"
manifest.viewingDirection = "left-to-right"

seq = manifest.sequence(ident="normal", label="Normal Order")

side = ['r','v'] # recto and verso side
folios = range(179) # number of folio pairs

for f in folios:
	folio = f + 1	
	for s in range(len(side)):
		output = "Creating " + msref + " f"+ ('%03d' % folio) + side[s]
		sys.stdout.write(output)
		sys.stdout.flush()
		sys.stdout.write("\b" * len(output))
		
		cvs = seq.canvas(ident="folio-%s%s" % (folio, side[s]), label="f %s%s" % (folio, side[s]))
		anno = cvs.annotation(ident="a-folio-%s%s" % (folio, side[s]))	

		# image is 0 padded by 3 characters
		img = anno.image(msref + "_f%03d%s" % (folio, side[s]), iiif=True)

		# Set image height and width, and canvas to same dimensions
		img.set_hw_from_iiif()	
		cvs.height = img.height
		cvs.width = img.width	
	
data = manifest.toString(compact=False)
fh = file(msref + '.json', 'w')
fh.write(data)
fh.close()
