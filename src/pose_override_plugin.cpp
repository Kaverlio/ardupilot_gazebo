// PoseOverridePlugin: subscribes to a pose topic and forces the model pose each update.
// Build (example for Gazebo 11):
//   g++ -shared -fPIC pose_override_plugin.cpp -o libPoseOverridePlugin.so \
//       $(pkg-config --cflags --libs gazebo)

#include <gazebo/common/Events.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/transport/transport.hh>
#include <gazebo/msgs/msgs.hh>

namespace gazebo
{
class PoseOverridePlugin : public ModelPlugin
{
public:
  void Load(physics::ModelPtr _model, sdf::ElementPtr _sdf) override
  {
    if (!_model)
    {
      gzerr << "PoseOverridePlugin: null model\n";
      return;
    }

    this->model = _model;
    this->matchName = _model->GetName();

    if (_sdf->HasElement("topic"))
    {
      this->topic = _sdf->Get<std::string>("topic");
    }
    if (_sdf->HasElement("match_name"))
    {
      this->matchName = _sdf->Get<std::string>("match_name");
    }

    this->node = transport::NodePtr(new transport::Node());
    this->node->Init(_model->GetWorld()->Name());
    this->sub = this->node->Subscribe(
        this->topic, &PoseOverridePlugin::OnPose, this, true);

    this->updateConnection = event::Events::ConnectWorldUpdateBegin(
        std::bind(&PoseOverridePlugin::OnUpdate, this));

    gzdbg << "PoseOverridePlugin loaded for model '" << this->model->GetName()
          << "' listening on topic '" << this->topic
          << "' match_name='" << this->matchName << "'\n";
  }

private:
  void OnPose(ConstPosePtr &_msg)
  {
    if (!this->matchName.empty() && _msg->has_name() &&
        _msg->name() != this->matchName)
    {
      return;
    }

    this->targetPose = msgs::ConvertIgn(*_msg);
    this->hasTarget = true;
  }

  void OnUpdate()
  {
    if (!this->hasTarget || !this->model)
      return;

    this->model->SetWorldPose(this->targetPose);
  }

private:
  physics::ModelPtr model;
  transport::NodePtr node;
  transport::SubscriberPtr sub;
  event::ConnectionPtr updateConnection;
  ignition::math::Pose3d targetPose;
  bool hasTarget{false};
  std::string topic{"~/pose_override"};
  std::string matchName;
};

GZ_REGISTER_MODEL_PLUGIN(PoseOverridePlugin)
}  // namespace gazebo
