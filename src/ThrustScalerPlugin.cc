#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/common/Events.hh>

#include <vector>
#include <string>
#include <iostream>
#include <functional>
#include <algorithm>

namespace gazebo
{
// Linearly scales rotor thrust from 1.0 down to 0.0 over a configured duration.
class ThrustScalerPlugin : public ModelPlugin
{
public:
  ThrustScalerPlugin() = default;

  void Load(physics::ModelPtr _model, sdf::ElementPtr _sdf) override
  {
    this->model = _model;
    this->world = _model->GetWorld();
    this->startSimTime = this->world->SimTime();

    std::cout << "[ThrustScalerPlugin] Load()" << std::endl;

    double scaleDurationMin = 10.0;
    if (_sdf && _sdf->HasElement("scale_duration_min"))
      scaleDurationMin = _sdf->Get<double>("scale_duration_min");

    this->scaleDurationSec = scaleDurationMin * 60.0;
    std::cout << "[ThrustScalerPlugin] scale_duration_min = "
              << scaleDurationMin
              << " (scaleDurationSec = " << this->scaleDurationSec << ")"
              << std::endl;

    if (_sdf && _sdf->HasElement("rotor_joint"))
    {
      sdf::ElementPtr rotorElem = _sdf->GetElement("rotor_joint");
      while (rotorElem)
      {
        // Joint name from the current <rotor_joint> tag.
        const std::string jointName = rotorElem->Get<std::string>();
        physics::JointPtr joint = this->model->GetJoint(jointName);
        if (joint)
        {
          this->rotorJoints.push_back(joint);
        }
        else
        {
          std::cout << "[ThrustScalerPlugin] Warning: joint '" << jointName
                    << "' not found on model '" << this->model->GetName()
                    << "'" << std::endl;
        }

        rotorElem = rotorElem->GetNextElement("rotor_joint");
      }
    }

    if (this->rotorJoints.empty())
    {
      std::cout << "[ThrustScalerPlugin] No rotor_joint entries found; "
                << "thrust scaling will be skipped." << std::endl;
    }

    this->updateConnection = event::Events::ConnectWorldUpdateBegin(
        std::bind(&ThrustScalerPlugin::OnUpdate, this,
                  std::placeholders::_1));
  }

private:
  void OnUpdate(const common::UpdateInfo &_info)
  {
    const double elapsedSec = (_info.simTime - this->startSimTime).Double();

    double scale = 1.0;
    if (this->scaleDurationSec > 0.0)
    {
      scale = 1.0 - elapsedSec / this->scaleDurationSec;
      scale = std::max(0.0, std::min(1.0, scale));
    }
    else
    {
      scale = 0.0;
    }

    for (auto &joint : this->rotorJoints)
    {
      const double currentForce = joint->GetForce(0);
      joint->SetForce(0, currentForce * scale);
    }
  }

private:
  physics::ModelPtr model;
  physics::WorldPtr world;
  common::Time startSimTime;
  double scaleDurationSec {10.0 * 60.0};
  std::vector<physics::JointPtr> rotorJoints;
  event::ConnectionPtr updateConnection;
};

GZ_REGISTER_MODEL_PLUGIN(ThrustScalerPlugin)
} // namespace gazebo
