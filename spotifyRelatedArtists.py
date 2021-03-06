import cgi
from google.appengine.api import users
import webapp2
import json
from urllib import urlopen

MAIN_PAGE_HTML = """
<html>
    <style>
    body{border: 20px solid #E5E5E5; margin: 0; padding: 0;}
    
    h1 {padding-left: 2cm; color:#ff7f00; font: 40px sans-serif; font-weight: bold;}
    h4 {padding-left: 2cm;  font: 15px sans-serif; font-weight: bold; }
    p{padding-left: 2cm; font: 15px sans-serif}
    div{padding-left: 2cm;} 

    p2 {padding-left: 2cm}  
    
    a:link {color: #ff7f00;}
    a:visited {color: #ff7f00;}
    a:hover { color: #FFBF7F;}
    
    .text-input{font-size: 100%}
    
    .btn-style{
    font-size: 120%;
    font-weight: bold;
    background:#ff7f00;
    color:#black;
    border-radius:8px;   
    padding:1em;
    margin-left:0em;
    line-height: 0px;
    cursor:pointer;
    height:5%
    }

label {
    font-size: 100%;
    background:#ff7f00;
    color:#fff;
    border-radius:8px;   
    padding:1em;
    margin:0em;
    cursor:pointer;
}

label:hover {
    background:#FFBF7F;   
}

input {
    margin-right:1em;   
}

input[type=text] {
  -webkit-appearance: none; -moz-appearance: none;
  display: block;
  margin: 0;
  width: 75%; height: 5%;
  font-size: 120%;
  border: 1px solid #bbb;
}
    

    
    </style>
  
  <body>
    <form action="/sign" method="post">
    <br>
    <h1>SPOTIFY RELATED ARTISTS VISUALISATION</h1>
    <h4>This app generates a visualisation of any Spotify artists by calling the spotify API and putting the data into a d3.js style visualisation
    <br>One stage gathers all the related artists to the requested artists
    <br>Two stage gathers all the related artists to those gathered at the first stage
    <br><br>For more details please visit <a href="http://myinspirationinformation.com/visualisation/d3-js/spotify-related-artists-app/" target="_blank">Inspiration Information</a></h4>
    <HR WIDTH=89% size=20 noshade color=#F4F4F4>
    <p>Choose how many stages of related artists would you like: <br><br></p>
    <p2><label><INPUT TYPE="Radio" Name="stages" Value="1" checked="checked">1-Stage</label>
    <label><INPUT TYPE="Radio" Name="stages" Value="2">2-Stage</label>
    <br>
    <br>
    <p>If you request 2 stage please be patient it may take a minute
    <br>
    <br> Enter the artist/band name(s). Use semi colons ; to separate multiple artists/bands: 
    </p>
    <div><input class="text-input" type="text" placeholder=" Enter band name" name="band" ></div>
    <br><div><input type="submit" class="btn-style" value="Make me my visualisation"></div>
    </form>
  </body>
</html>
"""

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_PAGE_HTML)

class Guestbook(webapp2.RequestHandler):
    def post(self):
        band = cgi.escape(self.request.get('band'))
        stages = cgi.escape(self.request.get('stages'))          
               
        #pull in bands split into a list 
        inputs = band.split(';')
        input_artist_id=[]
        #start up text strings to store nodes and links in json form for d3
        json_nodes = "{\"nodes\":[" 
        json_links = "],\"links\":["
        
        #fins ids for each artist in list
        for a in range(len(inputs)):
          artist=inputs[a].replace(" ", "%20").lower()
          art_url='https://api.spotify.com/v1/search?q='+artist+'&type=artist'
          urlout=urlopen(art_url).read()
          result=json.loads(urlout)
          if result['artists']['items']:
            input_artist_id.append(result['artists']['items'][0]['id'])
        
        if len(inputs)==len(input_artist_id):
            #iterate through each id find related artists
            artist_id=[]
            for id in input_artist_id:
              if id not in artist_id:
                artist_id.append(id)
                art_url='https://api.spotify.com/v1/artists/'+id
                urlout=urlopen(art_url).read()
                result=json.loads(urlout)
                nodes={'name':result['name'],'group':0,'popularity':result['popularity']}
                json_nodes = json_nodes + json.dumps(nodes) +','
              rel_url='https://api.spotify.com/v1/artists/'+id+'/related-artists'
              urlout=urlopen(rel_url).read()
              related=json.loads(urlout)
              
              #iterate through each related artist and add to the nodes and links   
              for r in range(20):
                if related['artists'][r]['uri'].replace("spotify:artist:","") not in artist_id:
                  artist_id.append(related['artists'][r]['uri'].replace("spotify:artist:",""))
                  if related['artists'][r]['uri'].replace("spotify:artist:","") in input_artist_id:
                    nodes={'name':related['artists'][r]['name'],'group':0,'popularity':related['artists'][r]['popularity']}
                  else:  
                    nodes={'name':related['artists'][r]['name'],'group':1,'popularity':related['artists'][r]['popularity']}
                  json_nodes = json_nodes + json.dumps(nodes) + ','
                edges={'source':artist_id.index(id),'target':artist_id.index(related['artists'][r]['uri'].replace("spotify:artist:","")), 
                       'value':1, 'distance':40+r*5}
                json_links = json_links + json.dumps(edges) + ','
            
            #if 2 stage is requested iterate through each related artist and find further related artists
            if stages=='2':
              artist_id2=list(set(artist_id)-set(input_artist_id))  
              for id in artist_id2:
                rel_url='https://api.spotify.com/v1/artists/'+id+'/related-artists'
                urlout=urlopen(rel_url).read()
                related=json.loads(urlout)
                  
                for r in range(20):
                  if related['artists'][r]['uri'].replace("spotify:artist:","") not in artist_id:
                    artist_id.append(related['artists'][r]['uri'].replace("spotify:artist:",""))
                    nodes={'name':related['artists'][r]['name'],'group':2,'popularity':related['artists'][r]['popularity']}
                    json_nodes = json_nodes + json.dumps(nodes) + ','
                  edges={'source':artist_id.index(id),'target':artist_id.index(related['artists'][r]['uri'].replace("spotify:artist:","")), 
                         'value':1, 'distance':40+r*5}
                  json_links = json_links + json.dumps(edges) + ','
                  
                  
            json_nodes = json_nodes[:-1]
            json_links = json_links[:-1]
            json_links = json_links + "]}"
            
            json_final = json_nodes + json_links

        outputstart = """<!DOCTYPE html>
    
    <style>
    body{border: 20px solid #E5E5E5; margin: 0; padding: 0;}
    
    .link {stroke: #ccc;}
    
    .node text {pointer-events: none;font: 10px sans-serif;    }
    
    h1 {padding-left: 2cm; color:#ff7f00; font: 40px sans-serif; font-weight: bold}
    h4 {padding-left: 2cm; font: 15px sans-serif; font-weight: bold}
    
    a:link {color: #ff7f00;}
    a:visited {color: #ff7f00;}
    a:hover { color: #FFBF7F;}
    
    .form-style{    
    font-size: 120%;
    font-weight: bold;
    background:#ff7f00;
    color:#black;
    border-radius:8px;   
    padding:1em;
    margin-left:0em;
    line-height: 0px;
    cursor:pointer;
    height:5%
    }
    
    </style>
    
    <body>
    <br>
    <h1>SPOTIFY RELATED ARTISTS VISUALISATION<h1/>
    <h4>Built by: <a href="http://myinspirationinformation.com/" target="_blank">Inspiration Information</a>
    <br><br>Thanks to:<a href="https://developer.spotify.com/web-api/" target="_blank">Spotify API</a> and 
    <a href="https://github.com/mbostock/d3/wiki/Gallery" target="_blank">Mike Bostock's D3 Project</a></h4>
    <br><HR WIDTH=89% size=20 noshade color=#F4F4F4>
    <h4><form action="http://spotify-related-artists-1.appspot.com/">
    <input type="submit" class="form-style" value="Make Another">
    </form>
    </h4>


    <script src="http://d3js.org/d3.v3.min.js"></script>
    
    <script type='text/javascript' src="http://labratrevenge.com/d3-tip/javascripts/d3.tip.v0.6.3.js"> </script>
    
    <script type="application/json" id="mis">
    """
        
        outputend = """</script>
    
    <script>
    //Constants for the SVG
    var width = 1000,
    height = 600;
    
    //Set up the colour scale
    var color = d3.scale.category20();
    
    //Set up the force layout
    var force = d3.layout.force()
    .charge(-120)
    .linkDistance(function(d) { return  d.distance; }) 
    .size([width, height]);
    
    //Append a SVG to the body of the html page. Assign this SVG as an object to svg
    var svg = d3.select(\"body\").append(\"svg\")
    .attr(\"width\", width)
    .attr(\"height\", height);
    
    //Read the data from the mis element 
    var mis = document.getElementById('mis').innerHTML;
    graph = JSON.parse(mis);
    
    //Creates the graph data structure out of the json data
    force.nodes(graph.nodes)
    .links(graph.links)
    .start();
    
    //Create all the line svgs but without locations yet
    var link = svg.selectAll(\".link\")
    .data(graph.links)
    .enter().append(\"line\")
    .attr(\"class\", \"link\")
    .style(\"stroke-width\", function (d) {return (d.value*0.5); });
    
    //Do the same with the circles for the nodes - no 
    //Changed
    var node = svg.selectAll(\".node\")
    .data(graph.nodes)
    .enter().append(\"g\")
    .attr(\"class\", \"node\")
    .call(force.drag);
    
    node.append(\"circle\")
    .attr(\"r\", 8)
    .attr(\"r\", function(d) { return d.popularity/5; })
    .style(\"fill\", function (d) { return color(d.group)
;
})
    
    node.append(\"text\")
    .attr(\"dx\", 10)
    .attr(\"dy\", \".35em\")
    .text(function(d) { return d.name });
    //End changed
    
    
   //Now we are giving the SVGs co-ordinates - the force layout is generating the co-ordinates which this code is using to update the attributes of the SVG elements
    force.on(\"tick\", function () {
    link.attr(\"x1\", function (d) {
    return d.source.x;
  })
    .attr(\"y1\", function (d) {
    return d.source.y;
    })
    .attr(\"x2\", function (d) {
    return d.target.x;
    })
    .attr(\"y2\", function (d) {
    return d.target.y;
    });
    
    //Changed
    
    d3.selectAll(\"circle\").attr(\"cx\", function (d) {
    return d.x;
    })
    .attr(\"cy\", function (d) {
    return d.y;
    });
    
    d3.selectAll(\"text\").attr(\"x\", function (d) {
    return d.x;
    })
    .attr(\"y\", function (d) {
    return d.y;
    });
    
    //End Changed
    
});
 </script>
 </body>
 </html>"""




        if len(inputs)==len(input_artist_id):
            self.response.write(outputstart)
            self.response.write(json_final)
            self.response.write(outputend)
        else:
            self.response.write(outputstart)
            self.response.write('</script><h4><br>You entered:<br><br>"')
            self.response.write(band)            
            self.response.write('"<br><br>One or more of your artists cant be found. Please try again</h4></body></html>')
           

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)