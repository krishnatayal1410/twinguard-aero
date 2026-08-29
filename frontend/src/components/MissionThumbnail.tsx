export type MissionVariant="start"|"cruise"|"shear"|"altitude"|"complete";
const images:Record<MissionVariant,string>={
 start:"/assets/replay/flight-start.jpg",
 cruise:"/assets/replay/cruise.jpg",
 shear:"/assets/replay/wind-shear.jpg",
 altitude:"/assets/replay/altitude-change.jpg",
 complete:"/assets/replay/mission-complete.jpg"
};
export default function MissionThumbnail({variant}:{variant:MissionVariant}){
 return <img className="mission-thumb-image" src={images[variant]} alt="" draggable={false}/>;
}