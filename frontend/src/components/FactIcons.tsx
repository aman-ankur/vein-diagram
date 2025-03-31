import React from 'react';
import {
  LocalHospital,
  Opacity,
  FitnessCenter,
  Favorite,
  Spa,
  Science,
  Coffee,
  Water,
  WbSunny,
  HealthAndSafety,
  Medication,
  LocalPharmacy,
  GppGood,
  ElectricalServices,
  MonitorHeart,
  HourglassEmpty,
  AlarmOn,
  BubbleChart,
  Bloodtype,
  Biotech,
  FastfoodOutlined,
  Coronavirus
} from '@mui/icons-material';

interface FactIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large' | number;
  color?: string;
}

const FactIcon: React.FC<FactIconProps> = ({ iconName, size = 'medium', color = 'primary' }) => {
  const iconProps = {
    fontSize: typeof size === 'string' ? size : undefined,
    sx: typeof size === 'number' ? { fontSize: size } : undefined,
    color: color as any
  };

  // Map icon names to Material UI icons
  switch (iconName.toLowerCase()) {
    case 'iron':
      return <FitnessCenter {...iconProps} />;
    case 'blood':
    case 'blooddrop':
      return <Opacity {...iconProps} />;
    case 'bloodvolume':
      return <Bloodtype {...iconProps} />;
    case 'heart':
    case 'heartrate':
      return <Favorite {...iconProps} />;
    case 'hearttest':
    case 'bloodpressure':
      return <MonitorHeart {...iconProps} />;
    case 'stress':
      return <HourglassEmpty {...iconProps} />;
    case 'test':
      return <Science {...iconProps} />;
    case 'cellgeneration':
    case 'dna':
      return <Biotech {...iconProps} />;
    case 'cholesterol':
    case 'lipids':
      return <BubbleChart {...iconProps} />;
    case 'diabetes':
      return <LocalHospital {...iconProps} />;
    case 'saliva':
    case 'water':
    case 'hydration':
      return <Water {...iconProps} />;
    case 'sun':
      return <WbSunny {...iconProps} />;
    case 'bacteria':
      return <Coronavirus {...iconProps} />;
    case 'thyroid':
    case 'hormones':
      return <HealthAndSafety {...iconProps} />;
    case 'calcium':
    case 'magnesium':
    case 'minerals':
      return <Medication {...iconProps} />;
    case 'coffee':
      return <Coffee {...iconProps} />;
    case 'fasting':
      return <AlarmOn {...iconProps} />;
    case 'electricity':
      return <ElectricalServices {...iconProps} />;
    case 'ph':
    case 'crystal':
    case 'metabolism':
      return <Science {...iconProps} />;
    case 'lungs':
    case 'respiratory':
      return <Spa {...iconProps} />;
    case 'whitebloodcell':
    case 'immunity':
      return <GppGood {...iconProps} />;
    case 'b12':
    case 'vitamins':
      return <LocalPharmacy {...iconProps} />;
    case 'digestion':
      return <FastfoodOutlined {...iconProps} />;
    // Add more icons as needed
    default:
      return <Science {...iconProps} />; // Default icon
  }
};

export default FactIcon; 