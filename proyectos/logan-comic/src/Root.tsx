import React from 'react';
import {Composition} from 'remotion';
import {LoganComic, TOTAL} from './Comic';

export const Root: React.FC = () => (
  <Composition id="LoganComic" component={LoganComic} durationInFrames={TOTAL} fps={30} width={1080} height={1920} />
);
