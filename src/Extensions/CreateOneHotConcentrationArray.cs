using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using AindBehaviorDeviceOlfactometerDataSchema;

[Combinator]
[Description("Creates an array of one-hot encoded concentration values for each olfactometer channel.")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class CreateOneHotConcentrationArray
{
    private int olfactometerCount = 12;
    public int OlfactometerCount
    {
        get { return olfactometerCount; }
        set { olfactometerCount = value; }
    }

    private double concentration = 1.0;
    public double Concentration
    {
        get { return concentration; }
        set { concentration = value; }
    }

    public IObservable<List<double>> Process(IObservable<Tuple<int, OlfactometerChannelConfig>> source)
    {
        return source.Select(value =>
        {
            var olfactometerIndex = value.Item1;
            var channelConfig = value.Item2;
            var numberOfChannels = 3 + (olfactometerCount-1) * 4; // 3 channels for the first olfactometer, 4 channels for each additional olfactometer
            var oneHotArray = new List<double>(new double[numberOfChannels]);
            var globalChannelIndex = olfactometerIndex == 0 ? channelConfig.ChannelIndex : (3 + (olfactometerIndex-1) * 4) + channelConfig.ChannelIndex;
            if (globalChannelIndex >= oneHotArray.Count)
            {
                throw new ArgumentOutOfRangeException("Calculated global channel index " + globalChannelIndex + " exceeds the one-hot array size.");
            }
            oneHotArray[globalChannelIndex] = concentration;
            return oneHotArray;
        });
    }
}
