import { useState, useEffect } from "react";
import parser from "html-react-parser";
import "./App.css";
import en from "./en.json";

// Dynamically require all monster JSONs in src/monsters
const monsterFiles = import.meta.glob('./monsters/*.json', { eager: true });
console.log('monsterFiles:', monsterFiles);
const monsterList = Object.entries(monsterFiles).map(([path, mod]) => {
  // Extract id from filename (cross-platform and more robust)
  const match = path.match(/[\\/]monsters[\\/]([^\/]+)\.json$/);
  if (!match) {
    console.error('Failed to match monster filename for path:', path);
    return null; // Or handle the error appropriately
  }
  const id = match[1];
  // Some environments put JSON under .default, some don't
  const data = mod.default ? mod.default : mod;
  return { id, data };
}).filter(m => m !== null); // Filter out any null entries if matching failed
console.log('monsterList:', monsterList);

function App() {
  const [front, setFront] = useState(1);
  const [isExpanded, setIsExpanded] = useState(false);
  // Check if monsterList is not empty before accessing the first element
  const initialSelected = monsterList.length > 0 ? monsterList[0].id : null;
  const initialMdata = monsterList.length > 0 ? monsterList[0].data : {};

  const [selected, setSelected] = useState(initialSelected);
  const [mdata, setMdata] = useState(initialMdata);
  const titles = en["monster-stat"];
  let hunterTurn, windUpTurn;

  console.log('Initial selected:', initialSelected);
  console.log('Initial mdata:', initialMdata);

  useEffect(() => {
    console.log('Selected monster changed:', selected);
    const found = monsterList.find((m) => m.id === selected);
    setMdata(found ? found.data : {});
    console.log('Updated mdata:', found ? found.data : {});
  }, [selected]);

  const frontBack = (e) => {
    setFront(!front);
  };
  const parse = (text) => {
    if (typeof text === "object") text = text.broken;
    if (!text) return "";
    if (typeof text === "string") text = [text];
    let r = "";
    text.forEach((t) => {
      t = t.replaceAll(
        /\[(blast|paralysis|poison|sleep|stun|dragon|fire|freeze|ice|thunder|water|r-dragon|r-fire|r-ice|r-thunder|r-water|bush|rock|pond|agility|armor|attack|closest|farthest|dodge|movement|range|break|move|hunter-turn|hunter-attack|supernova|nerg-dive|spike|claws|head|leg|tail|torso|wing|track|flash|sharpen|enraged|bubble|scales|amp|stench|shroom|bubble-off|bubble-bliss|attack-cards|egg|bleed|arkface)\]/g,
        (m, m1) => {
          return `<div className="icon-status ${m1}"><img src="icons/${m1}.png" alt=""></div>`;
        }
      );
      t = t.replaceAll("\n", "<br/>");
      t = t.replaceAll("\\", "<br/><br/>");
      t = t.replaceAll(/\*([^\*]+)\*/g, "<span className='em'>$1</span>");
      r += `<div>${t}</div>`;
    });
    return parser(r);
  };

  const toggleSelector = (e) => {
    // Check if the click is directly on the monster-selector div
    if (e.target === e.currentTarget) {
      setIsExpanded(!isExpanded);
    }
    // Remove e.stopPropagation() from here
    // e.stopPropagation();
  };

  // Minimalist selector
  return (
    <div className="App" onClick={(e) => {
      frontBack(e);
      // Removed this line to prevent collapsing on background click
      // setIsExpanded(false);
    }}>
      <div 
        className={`monster-selector ${isExpanded ? 'expanded' : ''}`} 
        onClick={toggleSelector}
      >
        <select 
          value={selected} 
          // Removed this onClick handler in the previous step
          // onClick={e => e.stopPropagation()} 
          onChange={e => {
            e.stopPropagation(); // Keep this to stop event propagation
            setSelected(e.target.value);
            setIsExpanded(false); // Keep this to collapse on selection
          }}
          style={{
            opacity: isExpanded ? 1 : 0,
            pointerEvents: isExpanded ? 'auto' : 'none'
          }}
        >
          {monsterList.length > 0 
            ? monsterList.map(m => <option value={m.id} key={m.id}>{en.monsters?.[m.id]||m.id}</option>) 
            : <option value="">No monsters found</option>}
        </select>
      </div>
      {/* Ensure mdata is not empty before mapping */}
      {Object.entries(mdata).length > 0 ? Object.entries(mdata).map(([id, m]) => (
        <div className={`cards ${front ? "front" : ""}`} key={id}>
          {Object.entries(m.behavior).map(([key, v]) => {
            if (front) {
              hunterTurn = null;
              windUpTurn = null;
              return (
                <div className={`card`} key={key}>
                  {Object.entries(v.actions).forEach(([i, e]) => {
                    if (e.type === "hunter") {
                      hunterTurn = i;
                    }
                    if (e.type === "wind-up") {
                      windUpTurn = i;
                    }
                  })}
                  {v.color && (
                    <div
                      className="coloring"
                      style={{
                        background: `radial-gradient(${v.color}00 25%, ${v.color}20 50%, ${v.color}40 75%, ${v.color}a0 100%)`,
                      }}
                    />
                  )}

                  {/* CARD AREA */}
                  <div className="card-area">
                    <div className="title">
                      {(m["behavior-names"] && m["behavior-names"][key]) ||
                        titles[id].behavior[key]}
                    </div>
                    {v.type && <div className={`icon type ${v.type}`} />}
                    {v.part && <div className={`icon part ${v.part}`} />}
                    <div className="target-area">
                      {windUpTurn !== null && (
                        <>
                          <div className={`icon hunter-turn`}>
                            <div className="num">
                              {v.actions[windUpTurn].turn}
                            </div>
                          </div>
                          <div className={`icon hunter-attack`}>
                            <div className="num">
                              {v.actions[windUpTurn].card}
                            </div>
                          </div>
                        </>
                      )}
                      <div className={`icon target ${v.target}`} />
                    </div>
                    <div className="action-area">
                      {Object.entries(v.actions).map(([i, a]) => {
                        // *ATTACK----------------------------------------------
                        if (a.type === "attack")
                          return (
                            <div className="action attack" key={i}>
                              <div className="num">{a.value}</div>
                              <div className="icon dodge">
                                <div className="num">{a.dodge}</div>
                              </div>
                              <div className="icon range">
                                <div className="num">{a.range}</div>
                              </div>
                              {a.dir === "n" ? (
                                <div className={`dir node`} />
                              ) : (
                                <div className={`dir`}>
                                  {Object.entries(a.dir || {}).map(([, d]) => (
                                    <div
                                      className={`dir-${d}`}
                                      key={`dir-${d}`}
                                    />
                                  ))}

                                  {a.atkdir &&
                                    Object.entries(a.atkdir || {}).map(
                                      ([, d]) => (
                                        <div
                                          className={`atkdir-${d} atk`}
                                          key={`atkdir-${d}`}
                                        />
                                      )
                                    )}
                                </div>
                              )}
                              {a.ele &&
                                [2, 4, 6, 8].map((d) => (
                                  <div
                                    className={`ele ${a.ele} dir-${d}`}
                                    key={d}
                                  />
                                ))}
                              {a.eff && <div className={`icon eff ${a.eff}`} />}
                            </div>
                          );

                        // *MOVE----------------------------------------
                        if (a.type === "move")
                          return (
                            <div className="action move" key={i}>
                              <div className={`move-dir dir-${a.dir}`}></div>
                              <div className={`num dir-${a.dir}`}>
                                {a.value}
                              </div>
                            </div>
                          );
                        // *ATTACK MOVE----------------------------------------
                        if (a.type === "atk-move")
                          return (
                            <div className="action atk-move" key={i}>
                              <div className={`move-dir dir-${a.dir}`}></div>
                              <div className={`num dir-${a.dir}`}>
                                {a.value}
                              </div>
                            </div>
                          );
                        // *ATTACK LOCK----------------------------------------
                        if (a.type === "atk-lock")
                          return (
                            <div className="action atk-lock" key={i}>
                              <div className="num">{a.value}</div>
                              <div className="icon dodge">
                                <div className="num">{a.dodge}</div>
                              </div>
                              <div className="icon range">
                                <div className="num">{a.range}</div>
                              </div>
                              {a.dir === "n" ? (
                                <div className={`dir node`} />
                              ) : (
                                <div className={`dir`}>
                                  {Object.entries(a.dir || {}).map(([, d]) => (
                                    <div
                                      className={`dir-${d}`}
                                      key={`dir-${d}`}
                                    />
                                  ))}

                                  {a.atkdir &&
                                    Object.entries(a.atkdir || {}).map(
                                      ([, d]) => (
                                        <div
                                          className={`atkdir-${d} atk`}
                                          key={`atkdir-${d}`}
                                        />
                                      )
                                    )}
                                </div>
                              )}
                              {a.ele &&
                                [2, 4, 6, 8].map((d) => (
                                  <div
                                    className={`ele ${a.ele} dir-${d}`}
                                    key={d}
                                  />
                                ))}
                              {a.eff && <div className={`icon eff ${a.eff}`} />}
                            </div>
                          );
                        // *TEXT-----------------------------------------
                        if (a.type === "text")
                          return <div className="text">{parse(a.value)}</div>;
                      })}
                    </div>

                    {/* BOTTOM TEXT AREA */}
                    <div classname="draganjegay">
                      {Object.entries(v.actions).map(([i, a]) => {
                        if (a.type === "bottom")
                          return <div className="bottom">{parse(a.value)}</div>;
                        if (a.type === "bottom-long")
                          return (
                            <div className="bottom-long">{parse(a.value)}</div>
                          );
                      })}
                    </div>                    {/* HUNTER AREA */}
                    {(hunterTurn !== null || v.extra) && (
                      <div className="hunter-area">
                        {v.extra && <div className={`icon ${v.extra}`}></div>}
                        {hunterTurn !== null && (
                          <>
                            <div className={`icon hunter-turn`}>
                              <div className="num">
                                {v.actions[hunterTurn].turn}
                              </div>
                            </div>
                            <div className={`icon hunter-attack`}>
                              <div className="num">
                                {v.actions[hunterTurn].card}
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            } else {
              return (
                <div className={`card back`} key={key}>
                  {v.color && (
                    <div
                      className="coloring"
                      style={{
                        background: `radial-gradient(${v.color}00 25%, ${v.color}20 50%, ${v.color}40 75%, ${v.color}a0 100%)`,
                      }}
                    />
                  )}
                  <div className="card-area">
                    <div className={`icon monster ${id}`} />
                    <div className={`icon target ${v.target}`} />
                    {v.part ? (
                      <div className={`icon part ${v.part}`} />
                    ) : (
                      <div className={`icon type ${v.type}`} />
                    )}
                  </div>
                </div>
              );
            }
          })}
        </div>
      )) : <div>No monster data loaded.</div>}
    </div>
  );
}

export default App;
